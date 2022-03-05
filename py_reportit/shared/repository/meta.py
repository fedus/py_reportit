import logging

from sqlalchemy import select, func
from sqlalchemy.sql import not_
from sqlalchemy.orm import Session
from random import choice
from uuid import UUID

from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.meta import Meta
from py_reportit.shared.model.meta_category_vote import MetaCategoryVote


logger = logging.getLogger(f"py_reportit.{__name__}")

class MetaRepository(AbstractRepository[Meta]):

    model = Meta

    def get_for_report_id(self, session: Session, report_id: int) -> Meta:
        return session.execute(select(Meta).where(Meta.report_id==report_id)).scalar()

    def get_random_among_lowest_votes(self, session: Session, user_id: UUID) -> Meta:
        metas_with_zero_votes = self.get_by(session, Meta.vote_count == 0, not_(Meta.category_votes.any(MetaCategoryVote.user_id == user_id)))

        if metas_with_zero_votes and len(metas_with_zero_votes):
            logger.debug(f"Returning random report meta with lowest votes (vote count: 0) for user {user_id}")
            return choice(metas_with_zero_votes)

        lowest_vote_count = session.execute(select(func.min(Meta.vote_count)).where(not_(Meta.category_votes.any(MetaCategoryVote.user_id == user_id)))).scalar()
        
        if not lowest_vote_count:
            logger.debug(f"No random report meta could be found user {user_id}, returning random choice ...")

            return session.execute(select(Meta).order_by(func.rand()).limit(1)).scalar()

        logger.debug(f"Returning random report meta among selection of vote count {lowest_vote_count} for user {user_id}")

        return choice(self.get_by(session, Meta.vote_count == lowest_vote_count, not_(Meta.category_votes.any(MetaCategoryVote.user_id == user_id))))
