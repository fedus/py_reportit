from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.user import User

class UserRepository(AbstractRepository[User]):

    model = User

    def get_by_id(self, session: Session, id: UUID) -> User:
        return session.execute(select(self.model).where(self.model.id==id)).scalar()

    def get_by_username(self, session: Session, username: str) -> User:
        return session.execute(select(self.model).where(self.model.username==username)).scalar()

    def delete_by_username(self, session: Session, username: str) -> None:
        return session.execute(delete(self.model).where(self.model.username==username))
