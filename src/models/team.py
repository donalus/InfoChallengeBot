from sqlalchemy import Column, Integer, String

from . import Base, UnsignedInt


class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(UnsignedInt, nullable=False)
    team_name = Column(String(255), nullable=False)
    team_role_id = Column(UnsignedInt, nullable=False)

    def __repr__(self):
        return f"<Team(team_id={self.team_id},team_name={self.team_name},team_role_id={self.team_role_id}"\
               f",guild_id={self.guild_id})>"
