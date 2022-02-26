from sqlalchemy import Column, Integer, String, ForeignKey
from . import Base, UnsignedInt


class TeamParticipant(Base):
    __tablename__ = 'team_participants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete=""))
    participant_id = Column(Integer, ForeignKey("participants.id"))
    guild_id = Column(UnsignedInt, nullable=False)

    def __repr__(self):
        return f"<TeamParticipant(id={self.id}, team_id={self.team_id}, " \
               f"participant_id={self.participant_id}, guild_id={self.guild_id})>"
