import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer
from sqlalchemy.dialects.mysql import BIGINT

from dotenv import load_dotenv

load_dotenv()
IS_PROD = os.environ['is_production'] == 'True'
DB_CONN_URI = os.environ['db_conn_uri']

engine = create_engine(DB_CONN_URI,
                       pool_size=50,
                       max_overflow=10,
                       pool_recycle=3600,
                       pool_pre_ping=True,
                       pool_use_lifo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Make an UnsignedInt that is compat with both sqlite and MariaDB
UnsignedInt = Integer()
UnsignedInt = UnsignedInt.with_variant(BIGINT(unsigned=True), 'mysql')
UnsignedInt = UnsignedInt.with_variant(BIGINT(unsigned=True), 'mariadb')

__all__ = ['Session', 'Registration', 'ConvoState', 'Participant',
           'TeamRegistration', 'Team', 'TeamParticipant', 'init_db']


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
        with Session() as session:
            create_test_data(session)

    log.info(f"[init_db: End]")


# PEP8 says these shouldn't be here, but putting these here avoids circular references within this module.
from models.registration import Registration
from models.convostate import ConvoState
from models.participant import Participant
from models.teamregistration import TeamRegistration
from models.team import Team
from models.teamparticipant import TeamParticipant
