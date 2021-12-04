from sqlalchemy import Column, Integer, String
from models import Base


class Participant(Base):
    __tablename__ = 'participants'

    discord_id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)
    team = Column(String(255))

    def __repr__(self):
        return f"<Participant(discord_id={self.discord_id}, email={self.email}, "\
               f"institution={self.institution}, team={self.team})>"
