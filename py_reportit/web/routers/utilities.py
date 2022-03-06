from dependency_injector.wiring import Provide, inject
from fastapi import Depends, APIRouter
from sqlalchemy.orm.session import Session

from py_reportit.web.dependencies import get_session
from py_reportit.shared.config.container import Container
from py_reportit.shared.repository.category import CategoryRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.shared.model import *


router = APIRouter(tags=["utilities"], prefix="/utilities")

@router.get("/services", response_model=list[str])
@inject
def get_services(
    report_answer_repository: ReportAnswerRepository = Depends(Provide[Container.report_answer_repository]),
    session: Session = Depends(get_session)
):
    """
    Retrieve a list of all services (city administration departments) found in the database.
    """
    return report_answer_repository.get_services(session)

@router.get("/categories")
@inject
def get_categories(
    category_repository: CategoryRepository = Depends(Provide[Container.category_repository]),
    session: Session = Depends(get_session)
):
    """
    Retrieve a list of all report categories in the database.
    """
    return category_repository.get_all(session)
