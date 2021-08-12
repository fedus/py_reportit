import requests
import logging
import sys

from PIL import Image
from PIL import ImageOps
from io import BytesIO

from py_reportit.post_processors.abstract_pp import AbstractPostProcessor
from py_reportit.model.report import Report
from py_reportit.model.meta import Meta


logger = logging.getLogger(__name__)

class PhotoDownload(AbstractPostProcessor):

    def process(self):
        logger.info("Starting PhotoDownload post processor")
        unprocessed_reports = self.report_repository.get_by(Report.photo_url != None, Report.meta.has(Meta.photo_downloaded==False))
        logger.info("Processing %d reports", len(unprocessed_reports))
        for report in unprocessed_reports:
            try:
                self.process_report(report)
            except KeyboardInterrupt:
                raise
            except:
                logger.error("Unexpected error:", sys.exc_info()[0])

    def process_report(self, report: Report):
        logging.debug("Processing %s", report)
        photo = self.download_photo(report.photo_url)
        self.resize_and_save_photo(photo, f"{self.config.get('PHOTO_DOWNLOAD_FOLDER')}/{report.id}.jpg", int(self.config.get('PHOTO_DOWNLOAD_QUALITY')))
        report.meta.photo_downloaded = True
        self.report_repository.session.commit()

    def download_photo(self, url: str) -> requests.models.Response:
        return requests.get(url)

    def resize_and_save_photo(self, photo_request: requests.models.Response, filename: str, quality: int) -> None:
        img = ImageOps.exif_transpose(Image.open(BytesIO(photo_request.content)))
        img.thumbnail(size=(1200,1200))
        img.save(filename, optimize=True, quality=quality)