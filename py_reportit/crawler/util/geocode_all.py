import sys

from time import sleep

from sqlalchemy.orm import sessionmaker

from py_reportit.shared.model.report import Report
from py_reportit.shared.model.meta import Meta
from py_reportit.shared.config import config
from py_reportit.crawler.service.geocoder import GeocoderService
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.config.db import engine
from py_reportit.crawler.post_processors.geocode_pp import Geocode

Session = sessionmaker(engine)

geocoder_service = GeocoderService(config)

success = []
repository_errors = []

start_id = int(config.get("START", -1))
end_id = int(config.get("END", -1))
only_missing_addresses = bool(int(config.get("ONLY_MISSING", 0)))
print_success = bool(int(config.get("PRINT_SUCCESS", 0)))

sleep_seconds = float(config.get("GEOCODE_DELAY_SECONDS", 0.5))

if start_id < 0 or end_id < 0:
    print("No start and / or end ID set, aborting.")
    quit()

with Session() as session:
    report_repository = ReportRepository(session)

    geocode_pp = Geocode(
        config,
        None,
        geocoder_service,
        report_repository,
        None,
        None,
        None
    )

    filter_critera = [Report.id >= start_id, Report.id <= end_id, Report.meta.has(Meta.address_polled==False)] if only_missing_addresses else [Report.id >= start_id, Report.id <= end_id]
    reports = report_repository.get_by(Report.id >= start_id, Report.id <= end_id)

    for report in reports:
        id = report.id
        try:
            print(f"Geocoding report {id}")
            print(geocoder_service.get_neighbourhood_and_street(report.latitude, report.longitude))
            geocode_pp.process_report(report)

            if print_success:
                print(report)
            success.append(report.id)
            sys.stdout.flush()
        except Exception as e:
            report_repository.session.rollback()
            print(f"Failed parsing or saving report {id}: {e}")
            sys.stdout.flush()
            repository_errors.append([id, e])
        finally:
            sleep(sleep_seconds)

print()
print("=== SUMMARY ===")
print(f"{len(repository_errors)} failures:")
for err in repository_errors:
    print(err)
print()

print(f"{len(success)} successes:")
print(", ".join(map(str, success)))

print("=== FINISHED ===")
