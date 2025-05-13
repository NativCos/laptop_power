#!/usr/bin/env python3
import os.path
import sys

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from model import LaptopPowerDeclarativeModelBase
from config import Config

DBEngine = create_engine("sqlite:///" + Config().dataBasePath,  # "sqlite:///" - ? what the fuck? see (https://datatracker.ietf.org/doc/html/rfc3986#section-3)
                         connect_args={'check_same_thread': False},
                         poolclass=StaticPool
                         )
DBSession = sessionmaker(DBEngine)


def create_schema():
    LaptopPowerDeclarativeModelBase.metadata.create_all(DBEngine)


if ':memory:' in Config().dataBasePath:
    create_schema()
elif not os.path.exists(Config().dataBasePath):
    create_schema()

if __name__ == '__main__':
    create_schema()
