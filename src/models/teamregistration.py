from sqlalchemy import Column, Integer, String
from . import Base, UnsignedInt


class TeamRegistration(Base):
    __tablename__ = 'team_registrations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(UnsignedInt, nullable=False)
    email = Column(String(255), nullable=False)
    team_name = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<TeamRegistration(id={self.id}, discord_id={self.discord_id}, " \
               f"email={self.email}, institution={self.institution}, role={self.role})>"
