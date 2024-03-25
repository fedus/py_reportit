import sys

from time import sleep

from dependency_injector.wiring import Provide, inject

from py_reportit.shared.config.container import run_with_container
from py_reportit.shared.config import config
from py_reportit.crawler.service.reportit_api import ReportItService, ReportNotFoundException
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository

# TODO: Fix - most notably, session injection in repo and reports_data, photo callback
@inject
def crawl_all(
    config: dict = Provide["config"],
    service: ReportItService = Provide["reportit_service"],
    report_repository: ReportRepository = Provide["report_repository"],
    answer_repository: ReportAnswerRepository = Provide["report_answer_repository"],
):
    success = []
    repository_errors = []
    non_existent_reports = []

    start_id = int(config.get("CRAWL_ALL_START", -1))
    end_id = int(config.get("CRAWL_ALL_END", -1))
    dry_run = bool(int(config.get("CRAWL_ALL_DRY_RUN", 0)))
    print_success = bool(int(config.get("CRAWL_ALL_PRINT_SUCCESS", 0)))

    sleep_seconds = int(config.get("CRAWL_SLEEP", 1))

    if start_id < 0 or end_id < 0:
        print("No start and / or end ID set, aborting.")
        quit()

    for id in range(start_id, end_id+1):
        try:
            print(f"Parsing report {id}")
            report = service.get_report_with_answers(id)
            report.meta.do_tweet = False
            for answer in report.answers:
                answer.meta.do_tweet = False
            if not dry_run:
                report_repository.update_or_create(report)
                answer_repository.update_or_create_all(report.answers)
            if print_success:
                print(report)
            success.append(report.id)
            sys.stdout.flush()
            sleep(sleep_seconds)
        except ReportNotFoundException as e:
            print(f"Report with id {id} does not exist")
            sys.stdout.flush()
            non_existent_reports.append(id)
        except Exception as e:
            if not dry_run:
                report_repository.session.rollback()
            print(f"Failed parsing or saving report {id}: {e}")
            sys.stdout.flush()
            repository_errors.append([id, e])

    print()
    print("=== SUMMARY ===")
    print(f"{len(non_existent_reports)} non existent reports:")
    print(", ".join(map(str, non_existent_reports)))
    print()

    print(f"{len(repository_errors)} failures:")
    for err in repository_errors:
        print(err)
    print()

    print(f"{len(success)} successes:")
    print(", ".join(map(str, success)))

    print("=== FINISHED ===")

if __name__ == "__main__":
    run_with_container(config, lambda: crawl_all())
else:
    print("Main module was imported, but is meant to run as standalone")
