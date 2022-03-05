from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from py_reportit.shared.model.meta_category_vote import MetaCategoryVote
from py_reportit.shared.repository.abstract_repository import AbstractRepository

class CategoryVoteRepository(AbstractRepository[MetaCategoryVote]):

    model = MetaCategoryVote

    def get_for_meta_and_user_id(self, session: Session, meta_id: int, user_id: UUID) -> MetaCategoryVote:
        return session.execute(select(MetaCategoryVote).where(MetaCategoryVote.meta_id==meta_id, MetaCategoryVote.user_id==user_id)).scalar()