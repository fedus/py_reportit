import logging

from uuid import uuid4, UUID
from sqlalchemy.orm import Session

from py_reportit.shared.model.meta_category_vote import MetaCategoryVote
from py_reportit.shared.repository.category import CategoryRepository
from py_reportit.shared.repository.category_vote import CategoryVoteRepository
from py_reportit.shared.repository.meta import MetaRepository

logger = logging.getLogger(f"py_reportit.{__name__}")


class VoteService:

    def __init__(self,
                 config: dict,
                 meta_repository: MetaRepository,
                 category_vote_repository: CategoryVoteRepository,
                 category_repository: CategoryRepository
                 ):
        self.config = config
        self.meta_repository = meta_repository
        self.category_vote_repository = category_vote_repository
        self.category_repository = category_repository

    def cast_vote(self, session: Session, user_id: UUID, report_id: int, category_id: int) -> bool:
        logger.info(f"Casting vote by user {user_id} for report {report_id} and category {category_id}")

        report_meta = self.meta_repository.get_for_report_id(session, report_id)
        category = self.category_repository.get_by_id(session, category_id)

        if not report_meta or not category:
            raise VoteException(f"Could not persist vote because report {report_id} or category {category_id} were not found")

        existing_vote = self.category_vote_repository.get_for_meta_and_user_id(session, report_meta.id, user_id)

        if existing_vote:
            logger.info(f"Changing existing vote from {existing_vote.category_id} to {category_id}")

            existing_vote.category_id = category_id
            session.commit()

            return True

        logger.info("Casting a new vote")

        new_vote = MetaCategoryVote(meta_id=report_meta.id, user_id=user_id, category_id=category_id)
        self.category_vote_repository.create(session, new_vote)

        return True

    def get_random_report_id_for_voting(self, session: Session, user_id: UUID) -> int:
        return self.meta_repository.get_random_among_lowest_votes(session, user_id).report_id

class VoteException(Exception):
    pass