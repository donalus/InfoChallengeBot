from sqlalchemy import Column, Integer, String
from . import Base, UnsignedInt


class Participant(Base):
    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(UnsignedInt, nullable=False)
    guild_id = Column(UnsignedInt, nullable=False)
    email = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)
    role = Column(String(255), default='Participant')

    def __repr__(self):
        return f"<Participant(id={self.id}, discord_id={self.discord_id}, " \
               f"email={self.email}, institution={self.institution}, role={self.role})>"
