from dependency_injector.wiring import Provide, inject
from fastapi import Depends, APIRouter, Path
from sqlalchemy.orm.session import Session

from py_reportit.shared.model.category import Category
from py_reportit.shared.model.user import User
from py_reportit.web.dependencies import get_current_active_admin, get_session
from py_reportit.shared.config.container import Container
from py_reportit.shared.repository.category import CategoryRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.shared.model import *
from py_reportit.web.schema.category import CategoryPost


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

@router.get("/category")
@inject
def get_categories(
    category_repository: CategoryRepository = Depends(Provide[Container.category_repository]),
    session: Session = Depends(get_session)
):
    """
    Retrieve a list of all report categories in the database.
    """
    return category_repository.get_all(session)

@router.post("/category", status_code=201)
@inject
def create_category(
    category: CategoryPost,
    category_repository: CategoryRepository = Depends(Provide[Container.category_repository]),
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_active_admin)
):
    """
    Create a new category.
    """
    new_category = Category(label=category.label)

    return category_repository.create(session, new_category)

@router.delete("/category/{category_id}", status_code=204)
@inject
def delete_category(
    category_id: int = Path(..., description="The ID of the category to be deleted"),
    category_repository: CategoryRepository = Depends(Provide[Container.category_repository]),
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_active_admin)
):
    """
    Delete a category.
    """
    return category_repository.delete_by_id(session, category_id)
