from fastapi import APIRouter, Path
from fastapi.responses import RedirectResponse


router = APIRouter(tags=["photos"], prefix="/photos")

@router.get("/{reportId}")
async def get_photo(reportId: int = Path(None, description="The report ID for which the photo should be retrieved")):
    """
    Retrieve the photo related to a given report ID.
    \f
    :param reportId: The related report ID
    """
    return RedirectResponse(f"/static/photos/{reportId}.jpg")
