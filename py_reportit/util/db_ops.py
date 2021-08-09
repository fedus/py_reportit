from py_reportit.config.db import engine
from py_reportit.model.orm_base import Base
from py_reportit.model.meta import Meta
from py_reportit.model.report import Report

def createTables():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    print('Select operation to execute:')
    print('  - Create all tables [0]')
    print()
    choice = int(input('Enter choice: '))

    if choice == 0: createTables()
