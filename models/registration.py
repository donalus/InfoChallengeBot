from sqlalchemy import Column, Integer, String
from models import Base


class Registration(Base):
    __tablename__ = 'registrations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Registration(id={self.id}, full_name={self.full_name}, email={self.email}, "\
               f"institution={self.institution})>"
