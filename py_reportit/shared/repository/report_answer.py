from sqlalchemy import update
from sqlalchemy.orm import Session

from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.report_answer import ReportAnswer
from py_reportit.shared.model.answer_meta import ReportAnswerMeta

class ReportAnswerRepository(AbstractRepository[ReportAnswer]):

    model = ReportAnswer

    def update(self, session: Session, entity: ReportAnswer) -> int:
        result = session.execute(
            update(ReportAnswer)
            .where(ReportAnswer.report_id == entity.report_id, ReportAnswer.order == entity.order)
            .values({column: getattr(entity, column) for column in ReportAnswer.__table__.columns.keys() if column != "id"})
        )
        session.commit()
        return result.rowcount

    def create(self, session: Session, entity: ReportAnswer) -> None:
        session.add(ReportAnswer(meta=ReportAnswerMeta(), **{column: getattr(entity, column) for column in ReportAnswer.__table__.columns.keys() if column != "id"}))
        session.commit()
