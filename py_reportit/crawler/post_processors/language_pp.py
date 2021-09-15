import logging
import sys

from pycld2 import detect

from py_reportit.crawler.post_processors.abstract_pp import AbstractPostProcessor
from py_reportit.shared.model.report import Report
from py_reportit.shared.model.report_answer import ReportAnswer
from py_reportit.shared.model.meta import Meta
from py_reportit.shared.model.answer_meta import ReportAnswerMeta


logger = logging.getLogger(f"py_reportit.{__name__}")

class Language(AbstractPostProcessor):

    def process(self, new_or_updated_reports: list[Report]):
        unprocessed_reports = self.report_repository.get_by(Report.meta.has(Meta.language==None))
        unprocessed_answers = self.report_answer_repository.get_by(ReportAnswer.meta.has(ReportAnswerMeta.language==None))
        logger.info("Processing %d reports and %d answers", len(unprocessed_reports), len(unprocessed_answers))
        self.process_reports(unprocessed_reports)
        self.process_answers(unprocessed_answers)

    def process_reports(self, unprocessed_reports: list[Report]) -> None:
        for report in unprocessed_reports:
            try:
                self.process_report(report)
                self.report_repository.session.commit()
            except KeyboardInterrupt:
                self.report_repository.session.rollback()
                raise
            except:
                self.report_repository.session.rollback()
                logger.error("Unexpected error:", sys.exc_info()[0])

    def process_report(self, report: Report) -> None:
        logger.info("Processing report id %d", report.id)
        # The below line is pretty naïve. Good enough for now.
        detected_language = detect(f"{report.title} {report.description}")[2][0][1]
        if detected_language:
            logger.info("Detected language %s for report %d", detected_language, report.id)
            report.meta.language = detected_language

    def process_answers(self, unprocessed_answers: list[ReportAnswer]):
        for answer in unprocessed_answers:
            try:
                self.process_answer(answer)
                self.report_answer_repository.session.commit()
            except KeyboardInterrupt:
                self.report_answer_repository.session.rollback()
                raise
            except:
                self.report_answer_repository.session.rollback()
                logger.error("Unexpected error:", sys.exc_info()[0])

    def process_answer(self, answer: ReportAnswer) -> None:
        logger.info("Processing answer id %d", answer.id)
        # The below line is pretty naïve. Good enough for now.
        detected_language = detect(answer.text)[2][0][1]
        if detected_language:
            logger.info("Detected language %s for answer %d", detected_language, answer.id)
            answer.meta.language = detected_language
