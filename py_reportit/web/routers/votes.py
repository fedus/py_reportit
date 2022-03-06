from uuid import UUID
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, APIRouter
from fastapi import Query, Path
from sqlalchemy.orm.session import Session

from py_reportit.web.dependencies import get_session
from py_reportit.shared.config.container import Container
from py_reportit.shared.service.vote_service import VoteService
from py_reportit.web.schema.report import Report
from py_reportit.shared.model import *
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.web.schema.vote import Vote


router = APIRouter(tags=["votes"], prefix="/votes")

@router.post("/cast/{reportId}/category/")
@inject
def cast_vote(
    vote: Vote,
    reportId: int = Path(None, description="The ID of the report for which to cast a vote"),
    vote_service: VoteService = Depends(Provide[Container.vote_service]),
    session: Session = Depends(get_session)
):
    """
    Cast a vote concerning a report's category.
    """
    return vote_service.cast_vote(session, vote.user_id, reportId, vote.category_id)

@router.get("/get-candidate/category", response_model=Report)
@inject
def get_candidate(
    user_id: UUID = Query(..., description="The user id or identifier for which a new random report to vote for should be fetched"),
    vote_service: VoteService = Depends(Provide[Container.vote_service]),
    report_repository: ReportRepository = Depends(Provide[Container.report_repository]),
    session: Session = Depends(get_session)
):
    """
    Retrieve a randomly selected report from those with the least amount of total votes and for which the given user id has not yet cast a vote.
    """
    return report_repository.get_by_id(session, vote_service.get_random_report_id_for_voting(session, user_id))
