from typing import Callable
import requests, re, logging, json

from base64 import b64decode
from bs4.element import ResultSet
from bs4 import BeautifulSoup
from datetime import datetime
from requests.models import Response
from time import sleep

from py_reportit.shared.model import *
from py_reportit.shared.model.meta import Meta
from py_reportit.shared.model.report import Report
from py_reportit.shared.model.report_answer import ReportAnswer
from py_reportit.shared.model.answer_meta import ReportAnswerMeta

logger = logging.getLogger(f"py_reportit.{__name__}")

class ReportItService:

    DATE_FORMAT_API = '%Y-%m-%d %H:%M:%S'
    DATE_FORMAT_WEB = '%d.%m.%Y %H:%M'

    def __init__(self, config):
        self.config = config

    def get_latest_truncated_report(self) -> Report:
        r = requests.get(self.config.get('REPORTIT_API_URL'))

        reports_string_raw = b64decode(re.search(self.config.get('REPORTIT_API_REPORTS_REGEX'), r.text).group(1))
        reports_string_escaped = reports_string_raw.decode('raw_unicode_escape')
        raw_reports = json.loads(reports_string_escaped)["reports"]

        most_recent_report = raw_reports[-1]
        return Report(**most_recent_report)

    def get_reports(self) -> list[Report]:
        r = requests.get(self.config.get('REPORTIT_API_URL'))
        unsorted_reports = list(
            map(
                lambda rawReport: Report(**{**rawReport,
                                         "created_at": datetime.strptime(rawReport['created_at'], self.DATE_FORMAT_API),
                                         "updated_at": datetime.strptime(rawReport['updated_at'], self.DATE_FORMAT_API)},
                                        meta=Meta()),
                r.json().get('reports')
            )
        )
        return sorted(unsorted_reports, key=lambda report: report.id)

    def get_bulk_reports(self, reportIds: list[int], stop_condition: Callable[[Report], bool]) -> list[Report]:
        logger.info(f"Fetching bulk reports, {reportIds[0]} - {reportIds[-1]}")

        reports = []

        for reportId in reportIds:
            try:
                logger.debug(f"Fetching report with id {reportId}")
                fetched_report = self.get_report_with_answers(reportId)
                reports.append(fetched_report)

                if stop_condition(fetched_report):
                    logger.info(f"Stop condition hit at report with id {reportId}, stopping bulk crawl")
                    break

                sleep(float(self.config.get("FETCH_REPORTS_BULK_DELAY_SECONDS")))
            except KeyboardInterrupt:
                raise
            except ReportNotFoundException:
                logger.debug(f"No report found with id {reportId}, skipping.")
            except requests.exceptions.Timeout:
                logger.warn(f"Retrieval of report with id {reportId} timed out after {self.config('FETCH_REPORTS_TIMEOUT_SECONDS')} seconds, skipping")
            except:
                logger.error(f"Error while trying to fetch report with id {reportId}, skipping", exc_info=True)

        return reports

    def get_report_with_answers(self, reportId: int) -> Report:
        r = self.fetch_report_page(reportId)

        if r.text.find("Sent on :") < 0:
            raise ReportNotFoundException(f"No report found with id {reportId}")

        soup = BeautifulSoup(r.text, 'html.parser')

        for br in soup.find_all("br"):
            br.replace_with("\n")

        report_properties = { "id": reportId }

        # Get title
        header_selection = soup.select(".panel-heading b")
        raw_header = header_selection[0].text.strip() if len(header_selection) else ""
        title_regex = re.search(r"(?<=\d\s:).*", raw_header)
        report_properties["title"] = title_regex.group().strip() if title_regex else None

        # Get description
        description_selection = soup.select(".panel-body .row .panel-default .panel-body")
        raw_description = description_selection[0].text.strip() if len(description_selection) else ""
        description_regex = re.search(r"Description\s:\n(.*)", raw_description, re.DOTALL)
        report_properties["description"] = description_regex.group(1).strip() if description_regex else None

        # Get status
        status_regex = re.search(r".*label\slabel-success.*", r.text)
        report_properties["status"] = "finished" if status_regex else "accepted"

        # Get created datetime
        created_selection = soup.select("table tbody tr:last-child td")
        raw_created = created_selection[0].text.strip() if len(created_selection) else None
        report_properties["created_at"] = datetime.strptime(raw_created, self.DATE_FORMAT_WEB) if raw_created else None

        # Get GPS, image url
        gps_and_image_urls_selection = soup.select(".img-thumbnail")
        report_properties["latitude"], report_properties["longitude"], report_properties["photo_url"] = None, None, None
        if len(gps_and_image_urls_selection) >= 1:
            # Only GPS position
            gps_url = gps_and_image_urls_selection[0]['src']
            gps_regex = re.search(r"center=(\d*\.\d*,\d*\.\d*)", gps_url)
            gps = gps_regex.group(1).strip() if gps_regex else None
            report_properties["latitude"], report_properties["longitude"] = gps.split(',') if gps else (None, None)
        if len(gps_and_image_urls_selection) == 2:
            # Both GPS position and image
            report_properties["photo_url"] = f"https://reportit.vdl.lu/photo/{reportId}.jpg"
            report_properties["thumbnail_url"] = f"https://reportit.vdl.lu/thumbnail/{reportId}.jpg"

        report = Report(**report_properties, meta=Meta())
        answers = self.get_answers(reportId, pre_fetched_page=r)
        report.answers = answers

        if len(answers):
            report.updated_at = answers[-1].created_at
        else:
            report.updated_at = report.created_at
            if report.status == 'finished':
                report.meta.closed_without_answer = True

        return report


    def get_answers(self, reportId: int, pre_fetched_page: Response = None) -> list[ReportAnswer]:
        r = pre_fetched_page or self.fetch_report_page(reportId)

        soup = BeautifulSoup(r.text, 'html.parser')

        for br in soup.find_all("br"):
            br.replace_with("\n")

        message_blocks = soup.select(".panel-body .row:nth-child(2) .panel.panel-default")
        message_dicts = map(self.extract_from_message_block, message_blocks)

        return [ReportAnswer(**message_dict, order=order, report_id=reportId, meta=ReportAnswerMeta()) for order, message_dict in enumerate(message_dicts)]

    def fetch_report_page(self, reportId: int) -> Response:
        return requests.post(self.config.get("REPORTIT_API_ANSWER_URL"), {"search_id": reportId}, timeout=int(self.config.get("FETCH_REPORTS_TIMEOUT_SECONDS")))

    @staticmethod
    def extract_from_message_block(block: ResultSet) -> dict:
        author = block.select(".panel-heading i")[0].text.strip()
        raw_header = block.select(".panel-heading")[0].text.strip()
        raw_timestamp = re.search(r"(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})", raw_header).group()
        created_at = datetime.strptime(raw_timestamp, '%d.%m.%Y %H:%M')
        closing = raw_header.split()[0].lower() == "closed"
        raw_text = block.select(".panel-body")
        text = raw_text[0].text.strip() if len(raw_text) else ""

        return {
            "author": author,
            "created_at": created_at,
            "closing": closing,
            "text": text
        }

class ReportNotFoundException(Exception):
    pass
