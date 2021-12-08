from pathlib import Path
import os
import ssl
import discord
from discord.ext import commands
import logging

from sqlalchemy import update
from validate_email_address import validate_email
from models import Session, Registration, ConvoState, Participant

from dotenv import load_dotenv

load_dotenv()

IS_PRODUCTION = os.getenv('is_production')
EVENT_NAME = os.getenv('event_name')
EVENT_GUILD_ID = int(os.getenv('event_guild_id'))
EVENT_CONTACT_EMAIL = os.getenv('event_contact_email')
DATA_DIR = os.getenv('data_dir')
BOT_KEY = os.getenv('bot_prefix')
LOGGING_STR = os.getenv('logging_str')
current_dir = Path('.')
data_path = current_dir / DATA_DIR


class RegistratorConvoFSM:
    _state: ConvoState
    member: discord.Member
    guild: discord.Guild
    session: Session
    conversation: str = 'registration'
    _state_funcs = ['initiate', 'email', 'confirm', 'registered']

    def __init__(self, log, session, guild, member):
        self.log = log
        self.session = session
        self.member = member
        self.guild = guild
        self._resume_state()

    def _resume_state(self):
        self.log.info(f"_resume_state: Enter")
        state_obj = self.session.query(ConvoState). \
            filter(ConvoState.discord_id == self.member.id,
                   ConvoState.guild_id == self.guild.id,
                   ConvoState.conversation == self.conversation).one_or_none()

        if state_obj is None:
            self.session.add(ConvoState(discord_id=self.member.id,
                                        guild_id=self.guild.id,
                                        conversation=self.conversation,
                                        state='initiate'))
            self.session.commit()
            state_obj = self.session.query(ConvoState). \
                filter(ConvoState.discord_id == self.member.id,
                       ConvoState.guild_id == self.guild.id,
                       ConvoState.conversation == self.conversation).one_or_none()
        self._state = state_obj
        self.log.info(f"_resume_state: Current State: {self.state.state}")

    @property
    def state(self):
        return self._state

    def exec(self, **kwargs):
        self.log.info(f"fsm.exec: {self.state.state}")
        response = None
        if self.state.state:
            state_func = eval(f"self._{self.state.state}")
            response = state_func(**kwargs)
        return response

    def next_state(self):
        self.log.info(f"next_state: old {self.state.state}")
        state_index = 0
        state_name = self.state.state
        if state_name in self._state_funcs:
            state_index = self._state_funcs.index(state_name)
            state_index += 1
        if state_index >= len(self._state_funcs):
            state_name = self._state_funcs[-1]
        else:
            state_name = self._state_funcs[state_index]
        self.session.execute(
            update(ConvoState).
                where(ConvoState.id == self.state.id).
                values(state=state_name)
        )
        self.session.commit()

        self.log.info(f"next_state: new {self.state.state}")

    def set_state_email(self, email):
        self.log.info(f"set_state_email: {email}")
        self.session.execute(
            update(ConvoState).
                where(ConvoState.id == self.state.id).
                values(email=email)
        )
        self.session.commit()
        self.state.email = email

    def set_state(self, state):
        self.log.info(f"set_state: {state}")
        self.state.state = state
        self.session.execute(
            update(ConvoState).
                where(ConvoState.id == self.state.id).
                values(state=state)
        )
        self.session.commit()

    def _initiate(self, **kwargs):
        self.log.info(f"_initiate: {kwargs}")
        self.next_state()
        return f"Hello {self.member.name}, it looks like you need to complete your registration " \
               f"for {self.guild.name}.\nPlease reply with your email address."

    def _email(self, **kwargs):
        self.log.info(f"_email: {kwargs}")
        response = "_email: No message?"
        if 'message' in kwargs:
            email = str(kwargs['message']).lower().strip()
            if validate_email(email):
                self.log.info(f"_email: valid email {email}")

                reg_obj = self.session.query(Registration). \
                    filter(Registration.email == email,
                           Registration.guild_id == self.guild.id).one_or_none()
                if reg_obj is None:
                    self.log.info(f"_email: unrecognized {email}")
                    response = f"I did not recognize the email \"{email}\". Would you like to try again? (Yes or No)"
                    self.set_state('unrecognized')
                else:
                    self.log.info(f"_email: recognized {email}")
                    response = f"I have found a registration for:\n" \
                               f"\tName: {reg_obj.full_name}\n" \
                               f"\tInstitution: {reg_obj.institution}\n" \
                               f"Is this you? [Reply with Yes or No]\n"
                    self.set_state_email(email)
                    self.next_state()
            else:
                self.log.info(f"_email: invalid email {email}")
                response = f"Hello {self.member.name}, that is not a valid email address.\n" \
                           f"Please reply with only the email address you used to register for {EVENT_NAME}."
        return response

    def _unrecognized(self, **kwargs):
        self.log.info(f"_unrecognized: {kwargs}")
        response = "_unrecognized: No message?"
        if 'message' in kwargs:
            message = str(kwargs['message']).strip().lower()
            if message == 'yes':
                response = f"Please reply with the email address you used to register for {EVENT_NAME}."
                self.set_state('email')
            elif message == 'no':
                self.set_state('unknown')
                response = self.exec(**kwargs)
            else:
                response = f"I'm sorry. I didn't understand your response.\n" \
                           f"Would you like to try another email address? (Yes or No)"

        return response

    def _confirm(self, **kwargs):
        self.log.info(f"_confirm: {kwargs}")
        response = '_confirm: No message?'
        if 'message' in kwargs:
            reg_obj = self.session.query(Registration). \
                filter(Registration.email == self.state.email,
                       Registration.guild_id == self.guild.id).one_or_none()
            if reg_obj is None:
                self.set_state('unknown')
                response = self.exec(**kwargs)
            else:
                message = str(kwargs['message']).lower().strip()
                if message == 'yes':

                    self.next_state()
                    response = self.exec(**kwargs)
                elif message == 'no':
                    response = f"Would you like to try another email address? (Yes or No)"
                    self.set_state('unrecognized')
                else:
                    response = f"I'm sorry, I didn't understand your response.\n" \
                               f"Please confirm you are:\n" \
                               f"\tName: {reg_obj.full_name}\n" \
                               f"\tInstitution: {reg_obj.institution}\n" \
                               f"By replying with Yes or No]\n"
        return response

    def _registered(self, **kwargs):
        self.log.info(f"_registered: {kwargs}")

        reg_obj = self.session.query(Registration). \
            filter(Registration.email == self.state.email,
                   Registration.guild_id == self.guild.id).one_or_none()

        if reg_obj is None:
            self.set_state('unknown')
            response = self.exec(**kwargs)
        else:
            participant = self.session.query(Participant).\
                filter(Participant.guild_id == self.guild.id,
                       Participant.discord_id == self.member.id).one_or_none()
            if participant is None:
                self.session.add(Participant(discord_id=self.member.id,
                                             guild_id=self.guild.id,
                                             email=reg_obj.email,
                                             institution=reg_obj.institution,
                                             role=reg_obj.role))

                self.session.commit()

            response = f"{self.member.name}, your registration is now complete. Congratulations!\n" \
                       f"You will now have access to the participate in the {EVENT_NAME} Discord."
        return response

    def _unknown(self, **kwargs):
        self.log.info(f"_unknown: {self.member.id} - {self.member.name}")
        return f"{self.member.name}, please email {EVENT_CONTACT_EMAIL} for support."

    async def sync_server_roles(self):
        # Add Discord Roles.
        participant = self.session.query(Participant). \
            filter(Participant.guild_id == self.guild.id,
                   Participant.discord_id == self.member.id).one_or_none()
        roles = dict([(r.name.lower(), int(r.id)) for r in self.guild.roles])
        if participant.role.lower() == 'participant':
            participant_role = self.guild.get_role(roles['participant'])
            institution_role = self.guild.get_role(roles[participant.institution.lower()])
            self.log.info(f"sync_server_roles: Participant\n"
                          f"\t{[participant_role, institution_role]}")
            await self.member.add_roles(participant_role)
            await self.member.add_roles(institution_role)
        else:
            self.log.info(f"sync_server_roles: {participant.role}\n"
                          f"\troles: {roles[participant.role.lower()]}")


class Registrator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(LOGGING_STR)
        self.log.info(f"Booting up Cog: Registrations")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot is True:
            return

        reg_fsm = RegistratorConvoFSM(Session(), member.guild, member)
        msg = reg_fsm.exec()
        await member.send(msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.command_prefix):
            return
        if not message.guild:
            session = Session()
            count = session.query(Participant).filter(Participant.discord_id == message.author.id).count()
            shared_guild_ids = [g.id for g in message.author.mutual_guilds]
            self.log.info(f"Author:\n"
                          f"\tID: {message.author.id}\n"
                          f"\tShared Guilds: {shared_guild_ids}\n"
                          f"\tParticipant Count: {count}")

            if EVENT_GUILD_ID in shared_guild_ids:
                guild = [g for g in message.author.mutual_guilds if g.id == EVENT_GUILD_ID].pop()
                member = guild.get_member(message.author.id)
                reg_fsm = RegistratorConvoFSM(self.log, Session(), guild, member)
                self.log.info(f"State is: {reg_fsm.state.state}")
                msg = reg_fsm.exec(message=message.content)
                await message.reply(msg)
                if reg_fsm.state.state == 'registered':
                    await reg_fsm.sync_server_roles()
            else:
                await message.reply(
                    f"I'm sorry. We don't share any servers, so I don't know how to help you."
                )

    @commands.command(name="help", aliases=["helpme", "help_me", "registration_help"])
    async def registration_help(self, ctx, *args):
        """
        Help on how to register
        :param ctx:
        :param args:
        :return:
        """
        if not ctx.guild:
            await ctx.send(
                f"Do you need help?"
            )

    @commands.command(name="register", alias=["reg", "registration", "register_me"])
    async def register(self, ctx, *args):
        """
        Register a new user
        :param ctx:
        :param args:
        :return:
        """
        if not ctx.guild:
            await ctx.send(
                f"So you want to register?"
            )


def setup(bot):
    bot.add_cog(Registrator(bot))
