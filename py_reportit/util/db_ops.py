from py_reportit.config.db import engine
from py_reportit.model import *

def createTables():
    orm_base.Base.metadata.create_all(engine)

if __name__ == '__main__':
    print('Select operation to execute:')
    print('  - Create all tables [0]')
    print()
    choice = int(input('Enter choice: '))

    if choice == 0: createTables()
