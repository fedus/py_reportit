from time import sleep

from sqlalchemy.orm import sessionmaker

from py_reportit.config import config
from py_reportit.service.reportit_api import ReportItService
from py_reportit.repository.report import ReportRepository
from py_reportit.config.db import engine

Session = sessionmaker(engine)

service = ReportItService(config)

success = []
fail = []

start_id = int(config.get("CRAWL_ALL_START", -1))
end_id = int(config.get("CRAWL_ALL_END", -1))

sleep_seconds = int(config.get("CRAWL_SLEEP", 1))

if start_id < 0 or end_id < 0:
    print("No start and / or end ID set, aborting.")
    quit()

with Session() as session:
    repository = ReportRepository(session)

    for id in range(start_id, end_id+1):
        try:
            print(f"Parsing report {id}")
            report = service.get_report_with_answers(id)
            report.meta.do_tweet = False
            for answer in report.answers:
                answer.meta.do_tweet = False
            repository.create(report)
            success.append(report.id)
            sleep(sleep_seconds)
        except Exception as e:
            fail.append(f"Failed parsing report {id}, {e}")


print(f"{len(fail)} failures:")
for err in fail:
    print(err)

print(f"{len(success)} successes.")
