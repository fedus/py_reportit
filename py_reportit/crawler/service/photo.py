import logging

from base64 import b64decode
from PIL import Image
from PIL import ImageOps
from io import BytesIO
from os.path import isfile

from py_reportit.shared.model.report import Report

logger = logging.getLogger(f"py_reportit.{__name__}")

class PhotoService:

    def __init__(self, config: dict):
        self.config = config

    def get_photo_path(self, reportId: int) -> str:
        return f"{self.config.get('PHOTO_DOWNLOAD_FOLDER')}/{reportId}.jpg"

    def photo_exists_for_report_id(self, reportId: int) -> bool:
        return isfile(self.get_photo_path(reportId))

    def process_base64_photo_if_not_downloaded_yet(self, report: Report, base_64_photo: str) -> None:
        if not self.photo_exists_for_report_id(report.id):
            logger.info(f"Photo does not exist yet for report {report.id}, processing ...")
            self.process_base64_photo(report, base_64_photo)
        else:
            logger.info(f"Photo already exists for report {report.id}, skipping")

    def process_base64_photo(self, report: Report, base_64_photo: str) -> None:
        logger.debug(f"Processing base64 encoded photo for report {report.id}")
        photo = Image.open(BytesIO(b64decode(base_64_photo)))
        self.resize_and_save_photo(photo, self.get_photo_path(report.id), int(self.config.get('PHOTO_DOWNLOAD_QUALITY')))

    def resize_and_save_photo(self, photo: Image, filename: str, quality: int) -> None:
        logger.debug(f"Resizing and saving photo with filename {filename} and quality {quality}")
        img = ImageOps.exif_transpose(photo)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(size=(1200,1200))
        img.save(filename, optimize=True, quality=quality)
