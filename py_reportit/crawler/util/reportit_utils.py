from py_reportit.shared.model.answer_meta import ReportAnswerMeta
from py_reportit.shared.model.answer_meta_tweet import AnswerMetaTweet
from py_reportit.shared.model.report_answer import ReportAnswer
from py_reportit.shared.model.meta_tweet import MetaTweet
from py_reportit.shared.model.meta import Meta
from py_reportit.shared.model.report import Report

def extract_ids(reports: list[Report]) -> list[int]:
    return list(map(lambda report: report.id, reports))

def get_lowest_and_highest_ids(reports: list[Report]) -> tuple[int]:
    ids = extract_ids(reports)
    return (min(ids), max(ids))

def get_last_tweet_id(report: Report) -> str:
    if report.answers and len(report.answers):
        all_answers: list[ReportAnswer] = report.answers
        all_answers_with_tweet_ids = list(filter(lambda answer: answer.meta.tweet_ids and len(answer.meta.tweet_ids), all_answers))
        if len(all_answers_with_tweet_ids):
            newest_answer = max(all_answers_with_tweet_ids, key=lambda answer: answer.order)
            answer_meta: ReportAnswerMeta = newest_answer.meta
            tweet_ids: list[AnswerMetaTweet] = answer_meta.tweet_ids
            return max(tweet_ids, key=lambda tweet_id: tweet_id.order).tweet_id
    report_meta: Meta = report.meta
    if report_meta.tweet_ids:
        tweet_ids: list[MetaTweet] = report_meta.tweet_ids
        follow_tweet_id = next(filter(lambda tweet_id: tweet_id.type == "follow", tweet_ids), False)
        if follow_tweet_id:
            return follow_tweet_id.tweet_id
        return max(tweet_ids, key=lambda tweet_id: tweet_id.order).tweet_id
    return None
