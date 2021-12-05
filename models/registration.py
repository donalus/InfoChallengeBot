from sqlalchemy import Column, Integer, String
from . import Base


def create_test_data(session):
    session.add_all([
        Registration(full_name='Tester McTesterson', email='tester99@umd.edu', institution='UMD'),
        Registration(full_name='Sailor Testbotten', email='gonavy@test.edu', institution='NAVY'),
    ])
    session.commit()


class Registration(Base):
    __tablename__ = 'registrations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Registration(id={self.id}, full_name={self.full_name}, email={self.email}, " \
               f"institution={self.institution})>"
