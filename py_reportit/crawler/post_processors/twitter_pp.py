import logging
import sys
import tweepy

from time import sleep
from sqlalchemy.sql.elements import and_

from py_reportit.crawler.post_processors.abstract_pp import PostProcessor
from py_reportit.shared.model.report import Report
from py_reportit.shared.model.meta import Meta
from py_reportit.shared.model.meta_tweet import MetaTweet
from py_reportit.shared.model.report_answer import ReportAnswer
from py_reportit.shared.model.answer_meta import ClosingType, ReportAnswerMeta
from py_reportit.shared.model.answer_meta_tweet import AnswerMetaTweet
from py_reportit.crawler.util.reportit_utils import get_last_tweet_id, calc_expected_status_length, twitter_wrap


logger = logging.getLogger(f"py_reportit.{__name__}")

CLOSING_TYPE_TO_EMOJI = {
    ClosingType.CLOSED: "✅",
    ClosingType.NOT_CLOSED: "📤",
    ClosingType.PARTIALLY_CLOSED: "☑️"
}

class Twitter(PostProcessor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tweet_service = TweetService(self.config)

    def process(self, new_or_updated_reports: list[Report]):
        self.process_reports()
        self.process_answers()

    def process_reports(self):
        if bool(int(self.config.get("TWITTER_POST_REPORTS"))):
            delay = int(self.config.get("TWITTER_DELAY_SECONDS"))
            unprocessed_reports = self.report_repository.get_by(
                Report.meta.has(Meta.do_tweet==True),
                Report.meta.has(Meta.tweeted==False)
            )
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

    def process_answers(self):
        if bool(int(self.config.get("TWITTER_POST_ANSWERS"))):
            delay = int(self.config.get("TWITTER_DELAY_SECONDS"))
            unprocessed_reports = self.report_repository.get_by(
                Report.meta.has(Meta.do_tweet==True),
                Report.meta.has(Meta.tweet_ids != None),
                Report.answers.any(
                    and_(ReportAnswer.meta.has(ReportAnswerMeta.do_tweet==True),
                    ReportAnswer.meta.has(ReportAnswerMeta.tweeted == False))
                )
            )
            logger.info("Processing %d reports with pending answers", len(unprocessed_reports))
            for report in unprocessed_reports:
                answers = sorted(
                    list(filter(lambda answer: answer.meta.do_tweet and not answer.meta.tweeted, report.answers)),
                    key=lambda answer: answer.order
                )
                logger.info("Processing %d answers", len(answers))
                for answer in answers:
                    try:
                        self.tweet_answer(report, answer)
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

    def tweet_report(self, report: Report) -> None:
        logger.info("Tweeting %s", report)
        media_filename = f"{self.config.get('PHOTO_DOWNLOAD_FOLDER')}/{report.id}.jpg" if report.photo_url != None else None
        title = f"{report.title}\n" if report.has_title else ""
        text = f"📩 {report.created_at.strftime('%Y-%m-%d')}\n{title}\n{report.description}"
        add_link = bool(int(self.config.get("TWITTER_ADD_REPORT_LINK")))
        link = self.config.get("REPORT_LINK_BASE")
        extra_parts = [f"💬 Follow this report's progress at {link}{report.id}"] if add_link else []

        tweet_ids = self.tweet_service.tweet_thread(text, report.latitude, report.longitude, media_filename=media_filename, extra_parts=extra_parts)
        message_tweet_ids = tweet_ids[:-1] if add_link else tweet_ids
        follow_progress_tweet_id = tweet_ids[-1:][0] if add_link else None

        tweet_metas = [MetaTweet(type="description", order=order, tweet_id=message_id) for order, message_id in enumerate(message_tweet_ids)]
        if add_link:
            tweet_metas.append(MetaTweet(type="follow", order=0, tweet_id=follow_progress_tweet_id))

        report.meta.tweeted = True
        report.meta.tweet_ids = tweet_metas
        self.report_repository.session.commit()

    def tweet_answer(self, report: Report, answer: ReportAnswer) -> None:
        last_tweet_id = get_last_tweet_id(report)

        if not last_tweet_id:
            logger.warn("Not tweeting %s because no last tweet id could be found", answer)
            return

        logger.info("Tweeting %s, answering to tweet id %s", answer, last_tweet_id)
        timestamp = answer.created_at.strftime('%Y-%m-%d')
        has_message_text = "with message:\n\n" if answer.text and answer.text != "" else "with no message."
        title_variant = "closed this report" if answer.closing else "updated this report"
        emoji = CLOSING_TYPE_TO_EMOJI[answer.meta.closing_type]
        title = f"{emoji} {answer.author} {title_variant} {has_message_text}"
        complete_text = f"{timestamp}\n{title}{answer.text}"

        tweet_ids = self.tweet_service.tweet_thread(complete_text, answer_to=last_tweet_id)
        tweet_metas = [AnswerMetaTweet(order=order, type="answer", tweet_id=message_id) for order, message_id in enumerate(tweet_ids)]

        if answer.meta.closing_type == ClosingType.PARTIALLY_CLOSED:
            partial_closing_text = "⚠️ It appears as if the city has stated that it will answer via snail mail, and the report is not actually closed.\n\nUnfortunately, this renders the outcome of this report opaque, and the progress (if any) will not be publicly accessible."
            partial_closing_tweet_ids = self.tweet_service.tweet_thread(partial_closing_text, answer_to=tweet_ids[-1])
            tweet_metas.extend([AnswerMetaTweet(order=order, type="partial_closure", tweet_id=message_id) for order, message_id in enumerate(partial_closing_tweet_ids)])

        answer.meta.tweeted = True
        answer.meta.tweet_ids = tweet_metas
        self.report_repository.session.commit()

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
        expected_status_length = calc_expected_status_length(text)
        logger.debug(f"Tweet length: expected: {expected_status_length}, raw: {len(text)}")
        if expected_status_length >= 280:
            logger.debug("Text length >= 280 chars, wrapping it")
            raw_wrapped = twitter_wrap(text, 274, replace_whitespace=False)
            parts = list(map(lambda part_tuple: f"{part_tuple[1]} {part_tuple[0]+1}/{len(raw_wrapped)}", enumerate(raw_wrapped)))
        parts.extend(extra_parts)
        last_status = answer_to
        tweet_ids = []
        for index, part in enumerate(parts):
            expected_part_length = calc_expected_status_length(part)
            logger.debug(f"Tweeting part {index+1}/{len(parts)} (length: expected: {expected_part_length}, raw: {len(part)})")
            tweet_params = { 'status': part }
            if index == 0 and media:
                tweet_params['media_ids'] = [media.media_id]
            if last_status:
                tweet_params['in_reply_to_status_id'] = last_status
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
                try:
                    last_status = self.api.update_status(**tweet_params).id
                except:
                    logger.error(f"Failed while tweeting, message length: expected: {expected_part_length}, raw: {len(part)}, params: {tweet_params}")
                    raise
                tweet_ids.append(last_status)
        return tweet_ids
