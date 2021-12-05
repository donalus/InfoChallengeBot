import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from dotenv import load_dotenv

load_dotenv()
IS_PROD = os.environ['is_production'] == 'True'
DB_CONN_URI = os.environ['db_conn_uri']

engine = create_engine(DB_CONN_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()

__all__ = ['Session', 'Registration', 'ConvoStep', 'Participant', 'init_db']


# Make Database
def init_db():
    import logging
    log = logging.getLogger(os.getenv('logging_str'))
    log.info(f"[init_db: Start] IsProd: {IS_PROD}")

    if not IS_PROD:
        log.info(f"[init_db: Drop]")
        Base.metadata.drop_all(engine)

    log.info(f"[init_db: Create] IsProd: {IS_PROD}")

    Base.metadata.create_all(engine)

    if not IS_PROD:
        log.info(f"[init_db: Add]")
        from .registration import create_test_data
        create_test_data(Session())

    log.info(f"[init_db: End]")


# PEP8 says these shouldn't be here, but putting these here avoids circular references within this module.
from models.registration import Registration
from models.convostep import ConvoStep
from models.participant import Participant
