import os
import sys

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, BOOLEAN
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.ext.declarative import declarative_base
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from configs.definitions import ROOT_DIR
import lib.utils as ut

Base = declarative_base()


class Mark(Base):

    __tablename__ = 'mark'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    mark = Column(Integer)
    mark_time = Column(DateTime)


class User(Base):

    __tablename__ = 'user'
    telegram_id = Column(Integer, primary_key=True)
    frequency = Column(Integer)
    start_hour = Column(Integer)
    end_hour = Column(Integer)
    minute = Column(Integer)
    active_flag = Column(BOOLEAN)

def initialize_bd() -> None:

    CONFIG_PATH = ROOT_DIR + '/configs/config.yaml'
    config = ut.read_config(CONFIG_PATH)
    bd_directory = config['bd_directory']
    bd_name = config['bd_name']

    if not os.path.exists(f"{ROOT_DIR}/{bd_directory}"):
        os.makedirs(f"{ROOT_DIR}/{bd_directory}")

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{ROOT_DIR}/{bd_directory}{bd_name}"

    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)

    return

