from sqlalchemy import TypeDecorator
from sqlalchemy_utils import ArrowType

from py_reportit.shared.config import config

class LocalizedArrow(TypeDecorator):
    '''Results returned as aware datetimes, not naive ones.'''

    cache_ok = True

    impl = ArrowType

    def process_result_value(self, value, dialect):
        # Ideally, config would be injected
        if value:
            return value.to(config.get("TIMEZONE", "local"))
