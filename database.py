from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import Base
from config import Config


DBEngine = create_engine(Config().dataBasePath)
DBSession = sessionmaker(DBEngine)


def create_schema():
    Base.metadata.create_all(DBEngine)


if __name__ == '__main__':
    create_schema()
