from sqlalchemy import update

from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.report_answer import ReportAnswer
from py_reportit.shared.model.answer_meta import ReportAnswerMeta

class ReportAnswerRepository(AbstractRepository[ReportAnswer]):

    model = ReportAnswer

    def update(self, entity: ReportAnswer) -> int:
        result = self.session.execute(
            update(ReportAnswer)
            .where(ReportAnswer.report_id == entity.report_id, ReportAnswer.order == entity.order)
            .values({column: getattr(entity, column) for column in ReportAnswer.__table__.columns.keys() if column != "id"})
        )
        self.session.commit()
        return result.rowcount

    def create(self, entity: ReportAnswer) -> None:
        self.session.add(ReportAnswer(meta=ReportAnswerMeta(), **{column: getattr(entity, column) for column in ReportAnswer.__table__.columns.keys() if column != "id"}))
        self.session.commit()
