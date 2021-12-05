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

if __name__ == '__main__':
    from .registration import Registration
    from .convostep import ConvoStep
    from .participant import Participant


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
        import models.registration
        session = Session()
        session.add_all([
            registration.Registration(full_name='Tester McTesterson', email='tester99@umd.edu', institution='UMD'),
            registration.Registration(full_name='Sailor Testbotten', email='gonavy@test.edu', institution='NAVY'),
        ])
        session.commit()

    log.info(f"[init_db: End]")
