from typing import Generic, Type, TypeVar
from abc import ABC

from sqlalchemy import select, update, Column
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func
from sqlakeyset import get_page

from py_reportit.shared.model.orm_base import Base

Model = TypeVar('Model', bound=Base)

class AbstractRepository(ABC, Generic[Model]):

    model: Type[Model] = None

    def __init__(self, session: Session):
        self.session = session
        super().__init__()

    def get_all(self, offset=None, limit=None) -> list[Model]:
        with_offset = lambda statement: statement.offset(offset) if (offset and offset >= 0) else statement
        with_limit = lambda statement: statement.limit(limit) if (limit and limit > 0) else statement

        select_statement = with_limit(with_offset(select(self.model).order_by(self.model.id.desc())))

        return self.session.execute(select_statement).scalars().all()

    def get_paged(self, page_size: int = 100, page=None, by: Column = None, asc: bool = True):
        # Using SQLAlchemy 1.x style select due to limitation of sqlakeyset
        by_column = by if by else self.model.id
        order_by = by_column.asc() if asc else by_column.desc()
        processed_order_by = [order_by, self.model.id.asc() if asc else self.model.id.desc()] if by_column != self.model.id else [by_column]
        q = self.session.query(self.model).order_by(*processed_order_by)
        return get_page(q, per_page=page_size, page=page)

    def get_by_id(self, id: int) -> Model:
        return self.session.execute(select(self.model).where(self.model.id==id)).scalar()

    def get_by(self, *where_clauses) -> list[Model]:
        return self.session.execute(select(self.model).where(*where_clauses)).scalars().all()

    def update(self, entity: Model) -> int:
        result = self.session.execute(
            update(self.model)
            .where(self.model.id == entity.id)
            .values({column: getattr(entity, column) for column in self.model.__table__.columns.keys()})
        )
        self.session.commit()
        return result.rowcount

    def update_or_create(self, entity: Model) -> bool or None:
        return self.update(entity) or self.create(entity)

    def update_or_create_all(self, entities: list[Model]) -> None:
        for entity in entities:
            self.update_or_create(entity)

    def create(self, entity: Model) -> None:
        self.session.add(entity)
        self.session.commit()

    def create_all(self, entities: list[Model]) -> None:
        self.session.add_all(entities)
        self.session.commit()

    def update_many(self, values: dict, *where_clauses) -> int:
        result = self.session.execute(
            update(self.model)
            .where(*where_clauses)
            .values(values)
        )
        self.session.commit()
        return result.rowcount

    def get_most_recent(self) -> Model:
        return self.session.execute(select(self.model).filter(self.model.id == self.session.query(func.max(self.model.id)).scalar())).scalar()

    def count_by(self, *where_clauses) -> int:
        return self.session.execute(select(func.count()).select_from(select(self.model).filter(*where_clauses).subquery())).scalars().one()

    def get_ids_by(self, *where_clauses) -> list[int]:
        return self.session.execute(select(self.model.id).where(*where_clauses)).scalars().all()
