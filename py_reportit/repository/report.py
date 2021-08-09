from sqlalchemy import select, update

from py_reportit.model.report import Report

class ReportRepository:

    def __init__(self, session):
        self.session = session

    def get_all(self) -> list[Report]:
        return self.session.execute(select(Report)).scalars().all()

    def get_by_id(self, id: int) -> Report:
        return self.session.execute(select(Report).where(Report.id==id)).scalar()

    def update(self, report: Report) -> int:
        result = self.session.execute(
            update(Report)
            .where(Report.id == report.id)
            .values({column: getattr(report, column) for column in Report.__table__.columns.keys()})
        )
        self.session.commit()
        return result.rowcount

    def update_or_create(self, report: Report) -> bool or None:
        return self.update(report) or self.create(report)

    def update_or_create_all(self, reports: list[Report]) -> None:
        for report in reports:
            self.update_or_create(report)

    def create(self, report: Report) -> None:
        self.session.add(report)
        self.session.commit()

    def create_all(self, reports: list[Report]) -> None:
        self.session.add_all(reports)
        self.session.commit()
