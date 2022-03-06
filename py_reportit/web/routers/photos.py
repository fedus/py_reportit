from fastapi import APIRouter, Path, HTTPException
from fastapi.responses import FileResponse
from os import path

from py_reportit.shared.config import config


router = APIRouter(tags=["photos"], prefix="/photos")

@router.get("/{reportId}")
async def get_photo(reportId: int = Path(None, description="The report ID for which the photo should be retrieved")):
    """
    Retrieve the photo related to a given report ID.
    \f
    :param reportId: The related report ID
    """
    photo_filename = f"{config.get('PHOTO_DOWNLOAD_FOLDER')}/{reportId}.jpg"
    if not path.isfile(photo_filename):
        raise HTTPException(status_code=404, detail=f"No photo found for report with id {reportId}")
    return FileResponse(photo_filename)
