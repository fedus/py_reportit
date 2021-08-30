import logging
import sys
import tweepy

from time import sleep
from textwrap import wrap

from py_reportit.post_processors.abstract_pp import AbstractPostProcessor
from py_reportit.model.report import Report
from py_reportit.model.crawl_result import CrawlResult
from py_reportit.model.meta import Meta
from py_reportit.model.meta_tweet import MetaTweet


logger = logging.getLogger(f"py_reportit.{__name__}")

class Twitter(AbstractPostProcessor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tweet_service = TweetService(self.config)

    def process(self, new_or_updated_reports: list[Report]):
        if bool(int(self.config.get("TWITTER_POST_REPORTS"))):
            delay = int(self.config.get("TWITTER_DELAY_SECONDS"))
            unprocessed_reports = self.report_repository.get_by(Report.meta.has(Meta.tweeted==False))
            logger.info("Processing %d reports", len(unprocessed_reports))
            for report in unprocessed_reports:
                try:
                    self.tweet_report(report)
                except KeyboardInterrupt:
                    raise
                except:
                    logger.error("Unexpected error:", sys.exc_info()[0])
                finally:
                    if self.config.get("DEV"):
                        logger.debug("Not sleeping since program is running in development mode")
                    else:
                        logger.debug("Sleeping for %d seconds", delay)
                        sleep(delay)
        if bool(int(self.config.get("TWITTER_POST_CRAWL_RESULTS"))):
            last_crawl_result: CrawlResult = self.crawl_result_repository.get_most_recent()
            if last_crawl_result and last_crawl_result.successful and (last_crawl_result.added or last_crawl_result.removed or last_crawl_result.marked_done):
                try:
                    self.tweet_crawl_result(last_crawl_result)
                except KeyboardInterrupt:
                    raise
                except:
                    logger.error("Unexpected error:", sys.exc_info()[0])


    def tweet_report(self, report: Report) -> None:
        logger.info("Tweeting %s", report)
        media_filename = f"{self.config.get('PHOTO_DOWNLOAD_FOLDER')}/{report.id}.jpg" if report.photo_url != None else None
        title = f"{report.title}\n" if report.has_title else ""
        text = f"{report.created_at.strftime('%Y-%m-%d')}\n{title}\n{report.description}"
        add_link = bool(int(self.config.get("TWITTER_ADD_REPORT_LINK")))
        link = self.config.get("REPORT_LINK_BASE")
        extra_parts = [f"Follow this report's progress at {link}{report.id}"] if add_link else []

        tweet_ids = self.tweet_service.tweet_thread(text, report.latitude, report.longitude, media_filename=media_filename, extra_parts=extra_parts)
        message_tweet_ids = tweet_ids[:-1] if add_link else tweet_ids
        follow_progress_tweet_id = tweet_ids[-1:][0] if add_link else None

        tweet_metas = [MetaTweet(type="description", order=order, tweet_id=message_id) for order, message_id in enumerate(message_tweet_ids)]
        if add_link:
            tweet_metas.append(MetaTweet(type="follow", order=0, tweet_id=follow_progress_tweet_id))

        report.meta.tweeted = True
        report.meta.tweet_ids = tweet_metas
        self.report_repository.session.commit()

    def tweet_crawl_result(self, crawl_result: CrawlResult) -> None:
        parts = ["Report-It website update:\n"]
        if crawl_result.added:
            parts.append(f"{crawl_result.added} new reports have been published")
        if crawl_result.removed:
            parts.append(f"{crawl_result.removed} reports have been removed")
        if crawl_result.marked_done:
            parts.append(f"{crawl_result.marked_done} reports have been marked as done")
        reportit_update = "\n".join(parts)
        self.tweet_service.tweet_thread(reportit_update)


class TweetService:

    def __init__(self, config):
        self.config = config
        self.do_authentication(
            self.config.get("TWITTER_API_KEY"),
            self.config.get("TWITTER_API_SECRET"),
            self.config.get("TWITTER_ACCESS_TOKEN"),
            self.config.get("TWITTER_ACCESS_SECRET")
        )

    def do_authentication(self, consumer_key, consumer_secret, access_token, access_token_secret):
        logger.debug("Setting Twitter authentication")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    def upload_media(self, filename):
        if self.config.get("DEV"):
            logger.debug("Not uploading media since program is running in development mode")
            return None
        logger.debug(f"Uploading media with filename {filename}")
        return self.api.media_upload(filename=filename)

    def tweet_thread(self, text, lat=None, lon=None, media_filename=None, extra_parts=[], answer_to=None):
        logger.debug("Sending tweet (as thread if necessary)")
        media = None
        if media_filename:
            media = self.upload_media(media_filename)
            logger.debug(f"Uploaded media: {media}")
        parts = [text]
        if len(text) > 280:
            logger.debug("Text longer than 280 chars, wrapping it")
            raw_wrapped = wrap(text, 270, replace_whitespace=False)
            parts = list(map(lambda part_tuple: f"{part_tuple[1]} {part_tuple[0]+1}/{len(raw_wrapped)}", enumerate(raw_wrapped)))
        parts.extend(extra_parts)
        last_status = answer_to
        tweet_ids = []
        for index, part in enumerate(parts):
            logger.debug(f"Tweeting part {index+1}/{len(parts)}")
            tweet_params = { 'status': part }
            if index == 0 and media:
                tweet_params['media_ids'] = [media.media_id]
            if last_status:
                tweet_params['in_reply_to_status_id'] = last_status.id
                tweet_params['auto_populate_reply_metadata'] = True
            if lat and lon:
                tweet_params['lat'] = lat
                tweet_params['long'] = lon
                tweet_params['display_coordinates'] = True
            logger.debug(f'Tweeting with params: {tweet_params}')
            if self.config.get("DEV"):
                logger.debug("Not sending tweet since program is running in development mode")
                return ["TWEET_ID1", "TWEET_ID2", "TWEET_ID3"]
            else:
                last_status = self.api.update_status(**tweet_params)
                tweet_ids.append(last_status.id)
        return tweet_ids
