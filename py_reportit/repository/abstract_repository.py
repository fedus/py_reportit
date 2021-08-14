from abc import ABC, abstractmethod

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func

class AbstractRepository(ABC):

    repository_type = None

    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[repository_type]:
        return self.session.execute(select(self.repository_type)).scalars().all()

    def get_by_id(self, id: int) -> repository_type:
        return self.session.execute(select(self.repository_type).where(self.repository_type.id==id)).scalar()

    def get_by(self, *where_clauses) -> list[repository_type]:
        return self.session.execute(select(self.repository_type).where(*where_clauses)).scalars().all()

    def update(self, entity: repository_type) -> int:
        result = self.session.execute(
            update(self.repository_type)
            .where(self.repository_type.id == entity.id)
            .values({column: getattr(entity, column) for column in self.repository_type.__table__.columns.keys()})
        )
        self.session.commit()
        return result.rowcount

    def update_or_create(self, entity: repository_type) -> bool or None:
        return self.update(entity) or self.create(entity)

    def update_or_create_all(self, entities: list[repository_type]) -> None:
        for entity in entities:
            self.update_or_create(entity)

    def create(self, entity: repository_type) -> None:
        self.session.add(entity)
        self.session.commit()

    def create_all(self, entities: list[repository_type]) -> None:
        self.session.add_all(entities)
        self.session.commit()

    def update_many(self, values: dict, *where_clauses) -> int:
        result = self.session.execute(
            update(self.repository_type)
            .where(*where_clauses)
            .values(values)
        )
        self.session.commit()
        return result.rowcount

    def get_most_recent(self) -> repository_type:
        return self.session.execute(select(self.repository_type).filter(self.repository_type.id == self.session.query(func.max(self.repository_type.id)).scalar())).scalar()

    def count_by(self, *where_clauses) -> int:
        return self.session.execute(select(func.count()).select_from(select(self.repository_type).filter(*where_clauses).subquery())).scalars().one()
