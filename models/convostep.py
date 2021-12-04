from sqlalchemy import Column, Integer, String
from models import Base


class ConvoStep(Base):
    __tablename__ = 'convo_step'

    discord_id = Column(Integer, primary_key=True, nullable=False)
    step = Column(Integer, default=0)

    def __repr__(self):
        return f"<ConvoStep(discord_id={self.discord_id}, step={self.step})>"
