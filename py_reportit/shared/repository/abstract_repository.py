from typing import Generic, Type, TypeVar
from abc import ABC

from sqlalchemy import select, update, Column
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.functions import func
from sqlakeyset import get_page

from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.model.page_with_count import PageWithCount

Model = TypeVar('Model', bound=Base)

class AbstractRepository(ABC, Generic[Model]):

    model: Type[Model] = None

    def get_all(self, session: Session, offset=None, limit=None) -> list[Model]:
        with_offset = lambda statement: statement.offset(offset) if (offset and offset >= 0) else statement
        with_limit = lambda statement: statement.limit(limit) if (limit and limit > 0) else statement

        select_statement = with_limit(with_offset(select(self.model).order_by(self.model.id.desc())))

        return session.execute(select_statement).scalars().all()

    def build_filter_query(self, session: Session, by: Column = None, asc: bool = True, and_cond = None, or_cond = None) -> Query:
        # Using SQLAlchemy 1.x style select due to limitation of sqlakeyset
        by_column = by if by else self.model.id
        order_by = by_column.asc() if asc else by_column.desc()
        processed_order_by = [order_by, self.model.id.asc() if asc else self.model.id.desc()] if by_column != self.model.id else [order_by]
        query = session.query(self.model).order_by(*processed_order_by)

        if and_cond and len(and_cond):
            query = query.filter(*and_cond)

        if or_cond and len(or_cond):
            query = query.filter(or_(*or_cond))

        return query


    def get_paged(self, session: Session, page_size: int = 100, page=None, **filter_Args) -> PageWithCount:
        q = self.build_filter_query(session, **filter_Args)

        return PageWithCount(page=get_page(q, per_page=page_size, page=page), total_count=q.count())

    def get_by_id(self, session: Session, id: int) -> Model:
        return session.execute(select(self.model).where(self.model.id==id)).scalar()

    def get_by(self, session: Session, *where_clauses) -> list[Model]:
        return session.execute(select(self.model).where(*where_clauses)).scalars().all()

    def update(self, session: Session, entity: Model) -> int:
        result = session.execute(
            update(self.model)
            .where(self.model.id == entity.id)
            .values({column: getattr(entity, column) for column in self.model.__table__.columns.keys()})
        )
        session.commit()
        return result.rowcount

    def update_or_create(self, session: Session, entity: Model) -> bool or None:
        return self.update(session, entity) or self.create(session, entity)

    def update_or_create_all(self, session: Session, entities: list[Model]) -> None:
        for entity in entities:
            self.update_or_create(session, entity)

    def create(self, session: Session, entity: Model) -> None:
        session.add(entity)
        session.commit()

    def create_all(self, session: Session, entities: list[Model]) -> None:
        session.add_all(entities)
        session.commit()

    def update_many(self, session: Session, values: dict, *where_clauses) -> int:
        result = session.execute(
            update(self.model)
            .where(*where_clauses)
            .values(values)
        )
        session.commit()
        return result.rowcount

    def get_most_recent(self, session: Session) -> Model:
        return session.execute(select(self.model).filter(self.model.id == session.query(func.max(self.model.id)).scalar())).scalar()

    def count_by(self, session: Session, *where_clauses) -> int:
        return session.execute(select(func.count()).select_from(select(self.model).filter(*where_clauses).subquery())).scalars().one()

    def get_ids_by(self, session: Session, *where_clauses) -> list[int]:
        return session.execute(select(self.model.id).where(*where_clauses)).scalars().all()

    def get_latest(self, session: Session, amount: int) -> list[Model]:
        entities = session.execute(select(self.model).order_by(self.model.id.desc()).limit(amount)).scalars().all()

        if entities:
            return sorted(entities, key=lambda entity: entity.id)

        return entities
