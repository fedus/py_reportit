import logging
import sys

from time import sleep

from py_reportit.crawler.post_processors.abstract_pp import AbstractPostProcessor
from py_reportit.shared.model.report import Report
from py_reportit.shared.model.meta import Meta


logger = logging.getLogger(f"py_reportit.{__name__}")

class Geocode(AbstractPostProcessor):

    def process(self, new_or_updated_reports: list[Report]):
        delay = float(self.config.get("GEOCODE_DELAY_SECONDS"))

        unprocessed_reports = self.report_repository.get_by(
            Report.meta.has(Meta.address_polled==False)
        )

        logger.info("Processing %d reports", len(unprocessed_reports))

        for report in unprocessed_reports:
            try:
                self.process_report(report)
            except KeyboardInterrupt:
                raise
            except:
                logger.error("Unexpected error:", sys.exc_info()[0])
            finally:
                logger.debug("Sleeping for %d seconds", delay)
                sleep(delay)

    def process_report(self, report: Report):
        logger.info("Processing %s", report)

        try:
            geocode_results = self.geocoder_service.get_neighbourhood_and_street(report.latitude, report.longitude)
            logger.info("Found geolocation for report: %s", str(geocode_results))
        except Exception as e:
            logger.error(f"Could not geolocate report {report.id}: {e}")
            raise

        report.meta.address_polled = True
        report.meta.address_street = geocode_results["street"]
        report.meta.address_postcode = geocode_results["postcode"]
        report.meta.address_neighbourhood = geocode_results["neighbourhood"]

        self.report_repository.session.commit()

