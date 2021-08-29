import logging
import sys

from py_reportit.post_processors.abstract_pp import AbstractPostProcessor
from py_reportit.model.report import Report


logger = logging.getLogger(f"py_reportit.{__name__}")
class AnswerFetch(AbstractPostProcessor):

    def process(self, new_or_updated_reports: list[Report]):
        unprocessed_reports = new_or_updated_reports
        logger.info("Processing %d reports", len(unprocessed_reports))
        for report in unprocessed_reports:
            try:
                self.process_report(report)
            except KeyboardInterrupt:
                raise
            except:
                logger.error("Unexpected error:", sys.exc_info()[0])

    def process_report(self, report: Report):
        logger.info("Processing %s", report)
        answers = self.api_service.get_answers(report.id)
        logger.info("Found %d answers for report", len(answers))
        self.report_answer_repository.update_or_create_all(answers)
