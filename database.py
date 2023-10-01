from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from model import LaptopPowerDeclarativeModelBase
from config import Config

DBEngine = create_engine(Config().dataBasePath,
                         connect_args={'check_same_thread': False},
                         poolclass=StaticPool
                         )
DBSession = sessionmaker(DBEngine)


def create_schema():
    LaptopPowerDeclarativeModelBase.metadata.create_all(DBEngine)


if ':memory:' in Config().dataBasePath:
    create_schema()

if __name__ == '__main__':
    create_schema()
