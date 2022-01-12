from sqlalchemy import Column, Integer, String
from . import Base


class ConvoState(Base):
    __tablename__ = 'convo_state'

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(Integer, nullable=False)
    guild_id = Column(Integer, nullable=False)
    conversation = Column(String, nullable=False)
    state = Column(String, nullable=False)
    email = Column(String)

    def __repr__(self):
        return f"<ConvoStep(guild_id={self.guild_id}, discord_id={self.discord_id}, "\
                f"conversation={self.conversation}, state={self.state}, email={self.email})>"
