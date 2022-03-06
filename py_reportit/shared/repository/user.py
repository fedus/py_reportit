from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.user import User

class UserRepository(AbstractRepository[User]):

    model = User
