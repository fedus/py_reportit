from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.category import Category

class CategoryRepository(AbstractRepository[Category]):

    model = Category
