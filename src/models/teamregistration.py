from sqlalchemy import Column, Integer, String
from . import Base, UnsignedInt


class TeamRegistration(Base):
    __tablename__ = 'team_registrations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(UnsignedInt, nullable=False)
    email = Column(String(255), nullable=False)
    team_name = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<TeamRegistration(id={self.id}, guild_id={self.guild_id}, " \
               f"email={self.email}, team_name={self.team_name})>"
