from sqlalchemy import Column, Integer, String
from . import Base, UnsignedInt

from dotenv import load_dotenv
import os

load_dotenv()
EVENT_GUILD_ID = os.getenv('event_guild_id')


def create_test_data(session):
    session.add_all([
        Registration(full_name='Testudo Turtle',
                     email='umd@test.test',
                     institution='UMD',
                     guild_id=EVENT_GUILD_ID),
        Registration(full_name='Bill the Goat',
                     email='navy@test.test',
                     institution='NAVY',
                     guild_id=EVENT_GUILD_ID),
        Registration(full_name='Chip Truegrit',
                     email='umbc@test.test',
                     institution='UMBC',
                     guild_id=EVENT_GUILD_ID),
        Registration(full_name='Testora Raptora',
                     email='mc@test.test',
                     institution='MC',
                     guild_id=EVENT_GUILD_ID),
        Registration(full_name='Judgy McJudgypants',
                     email='judge@test.test',
                     institution='UMD',
                     guild_id=EVENT_GUILD_ID,
                     role='Judge'),
        Registration(full_name='Helper O\'Hara',
                     email='volunteer@test.test',
                     institution='UMD',
                     guild_id=EVENT_GUILD_ID,
                     role='Volunteer'),
        Registration(full_name='Molly Mentorson',
                     email='mentor@test.test',
                     institution='UMD',
                     guild_id=EVENT_GUILD_ID,
                     role='Mentor'),
    ])
    session.commit()


class Registration(Base):
    __tablename__ = 'registrations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(UnsignedInt, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)
    role = Column(String(255), default='Participant')

    def __repr__(self):
        return f"<Registration(id={self.id}, full_name={self.full_name}, email={self.email}, " \
               f"institution={self.institution}, guild_id={self.guild_id})>"
