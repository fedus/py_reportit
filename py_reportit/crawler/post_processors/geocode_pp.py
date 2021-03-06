import logging

from time import sleep
from sqlalchemy.orm import Session

from py_reportit.crawler.post_processors.abstract_pp import PostProcessor
from py_reportit.shared.model.report import Report
from py_reportit.shared.model.meta import Meta


logger = logging.getLogger(f"py_reportit.{__name__}")

class Geocode(PostProcessor):

    immediate_run = True

    def process(self, session: Session, new_or_updated_reports: list[Report]):
        if not int(self.config.get("GEOCODE_ACTIVE")):
            logger.info("Geocoding not active, skipping")
            return

        delay = float(self.config.get("GEOCODE_DELAY_SECONDS"))

        unprocessed_reports = self.report_repository.get_by(
            session,
            Report.latitude != None,
            Report.longitude != None,
            Report.meta.has(Meta.address_polled==False)
        )

        logger.info("Processing %d reports", len(unprocessed_reports))

        for report in unprocessed_reports:
            try:
                self.process_report(session, report)
            except KeyboardInterrupt:
                raise
            except:
                logger.error(f"Unexpected error while processing report {report}", exc_info=True)
            finally:
                logger.debug("Sleeping for %d seconds", delay)
                sleep(delay)

    def process_report(self, session: Session, report: Report):
        logger.info(f"Processing report {report.id}")

        try:
            geocode_results = self.geocoder_service.get_neighbourhood_and_street(report.latitude, report.longitude)
            logger.info("Found geolocation for report: %s", str(geocode_results))
        except Exception as e:
            logger.error(f"Could not geolocate report {report.id}: {e}")
            raise

        report.meta.address_polled = True
        report.meta.address_street = geocode_results["street"]
        report.meta.address_postcode = int(geocode_results["postcode"]) if geocode_results["postcode"] else None
        report.meta.address_neighbourhood = geocode_results["neighbourhood"]

        session.commit()

