from pathlib import Path
import os
import ssl
import discord
from discord.ext import commands
from discord.ui import View, Button
import logging

from sqlalchemy import update, delete
from validate_email_address import validate_email
from models import Session, Registration, ConvoState, Participant

from dotenv import load_dotenv

from pycord.discord import ButtonStyle

load_dotenv()

IS_PRODUCTION = os.getenv('is_production')
EVENT_NAME = os.getenv('event_name')
EVENT_GUILD_ID = int(os.getenv('event_guild_id'))
EVENT_CONTACT_EMAIL = os.getenv('event_contact_email')
EVENT_BOT_CHANNEL_ID = int(os.getenv('event_bot_channel_id'))
DATA_DIR = os.getenv('data_dir')
BOT_KEY = os.getenv('bot_prefix')
LOGGING_STR = os.getenv('logging_str')
current_dir = Path('.')
data_path = current_dir / DATA_DIR


def is_in_guild(guild_id):
    async def guild_predicate(ctx):
        return ctx.guild and ctx.guild.id == guild_id

    return commands.check(guild_predicate)


def is_in_channel(channel_id):
    async def channel_predicate(ctx):
        return ctx.channel and ctx.channel.id == channel_id

    return commands.check(channel_predicate)


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
        self.log.info(f"fsm._resume_state: {self.state.state}")

    @property
    def state(self):
        return self._state

    def exec(self, **kwargs):
        self.log.info(f"fsm.exec: {self.state.state}")
        response = None
        view = None
        if self.state.state:
            state_func = eval(f"self._{self.state.state}")
            response, view = state_func(**kwargs)
        return response, view

    def next_state(self):
        state_index = 0
        state_name = self.state.state
        if state_name in self._state_funcs:
            state_index = self._state_funcs.index(state_name)
            state_index += 1
        if state_index >= len(self._state_funcs):
            state_name = self._state_funcs[-1]
        else:
            state_name = self._state_funcs[state_index]
        self.set_state(state_name)

    def set_state_email(self, email):
        self.log.info(f"fsm.set_state_email: {email}")
        self.session.query(ConvoState). \
            filter(ConvoState.id == self.state.id). \
            update({'email': email})
        self.session.commit()
        self.state.email = email

    def set_state(self, state):
        self.log.info(f"fsm.set_state: {state}")
        self.state.state = state
        self.session.query(ConvoState). \
            filter(ConvoState.id == self.state.id). \
            update({'state': state})
        self.session.commit()

    def _initiate(self, **kwargs):
        self.log.info(f"fsm._initiate: {kwargs}")
        self.next_state()
        response = f"Hello {self.member.name}, it looks like you need to complete your registration " \
                   f"for {self.guild.name}.\nPlease reply with your email address."
        return response, None

    def _email(self, **kwargs):
        self.log.info(f"fsm._email: {kwargs}")
        response = "_email: No message?"
        view = None
        if 'message' in kwargs:
            email = str(kwargs['message']).lower().strip()
            if validate_email(email):
                self.log.info(f"fsm._email: valid email {email}")

                reg_obj = self.session.query(Registration). \
                    filter(Registration.email == email,
                           Registration.guild_id == self.guild.id).one_or_none()
                if reg_obj is None:
                    self.log.info(f"fsm._email: unrecognized {email}")
                    response = f"I did not recognize the email \"{email}\". " \
                               f"Would you like to try again? (Reply with Yes or No)"
                    view = View()
                    yes_button = Button(label="Yes", emoji="✔", style=ButtonStyle.green)
                    view.add_item(yes_button)
                    no_button = Button(label="No", emoji="❌", style=ButtonStyle.red)
                    view.add_item(no_button)
                    self.set_state('unrecognized')
                else:
                    self.log.info(f"fsm._email: recognized {email}")
                    response = f"I have found a registration for:\n" \
                               f"\tName: {reg_obj.full_name}\n" \
                               f"\tInstitution: {reg_obj.institution}\n" \
                               f"Is this you? (Reply with Yes or No)\n"
                    view = View()

                    class YesButton(Button):
                        def __init__(self, convo_state):
                            self.convo_state = convo_state
                            super().__init__(label="Yes", emoji="✔", style=ButtonStyle.green)

                        async def callback(self, interaction):
                            msg, _ = self.convo_state.exec(message="yes")
                            await self.convo_state.sync_server_roles()
                            await interaction.delete_original_message()
                            await interaction.followup.send_message(msg)

                    yes_button = YesButton(self)
                    view.add_item(yes_button)

                    class NoButton(Button):
                        def __init__(self, convo_state):
                            self.convo_state = convo_state
                            super().__init__(label="No", emoji="❌", style=ButtonStyle.red)

                        async def callback(self, interaction):
                            msg, _ = self.convo_state.exec(message="no")
                            await interaction.response.edit_original_message("...")
                            await interaction.followup.send_message(msg)

                    no_button = NoButton(self)
                    view.add_item(no_button)
                    self.set_state_email(email)
                    self.next_state()
            else:
                self.log.info(f"fsm._email: invalid email {email}")
                response = f"Hello {self.member.name}, that is not a valid email address.\n" \
                           f"Please reply with only the email address you used to register for {EVENT_NAME}."
        return response, view

    def _unrecognized(self, **kwargs):
        self.log.info(f"fsm._unrecognized: {kwargs}")
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
                           f"Would you like to try another email address? (Reply with Yes or No)"

        return response, None

    def _confirm(self, **kwargs):
        self.log.info(f"fsm._confirm: {kwargs}")
        response = '_confirm: No message?'
        view = None
        if 'message' in kwargs:
            reg_obj = self.session.query(Registration). \
                filter(Registration.email == self.state.email,
                       Registration.guild_id == self.guild.id).one_or_none()
            if reg_obj is None:
                self.set_state('unknown')
                response, view = self.exec(**kwargs)
            else:
                message = str(kwargs['message']).lower().strip()
                if message == 'yes':

                    self.next_state()
                    response, view = self.exec(**kwargs)
                elif message == 'no':
                    response = f"Would you like to try another email address? (Reply with Yes or No)"
                    self.set_state('unrecognized')
                else:
                    response = f"I'm sorry, I didn't understand your response.\n" \
                               f"Please confirm you are:\n" \
                               f"\tName: {reg_obj.full_name}\n" \
                               f"\tInstitution: {reg_obj.institution}\n" \
                               f"(Reply with Yes or No)\n"
        return response, view

    def _registered(self, **kwargs):
        self.log.info(f"fsm._registered: {kwargs}")

        reg_obj = self.session.query(Registration). \
            filter(Registration.email == self.state.email,
                   Registration.guild_id == self.guild.id).one_or_none()

        view = None
        if reg_obj is None:
            self.set_state('unknown')
            response, view = self.exec(**kwargs)
        else:
            participant = self.session.query(Participant). \
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
        return response, view

    def _unknown(self, **kwargs):
        self.log.info(f"fsm._unknown: {self.member.id} - {self.member.name}")
        response = f"{self.member.name}, please email {EVENT_CONTACT_EMAIL} for support."
        return response, None

    async def sync_server_roles(self):
        # Add Discord Roles.
        participant = self.session.query(Participant). \
            filter(Participant.guild_id == self.guild.id,
                   Participant.discord_id == self.member.id).one_or_none()
        roles = dict([(r.name.lower(), int(r.id)) for r in self.guild.roles])
        if participant.role.lower() == 'participant':
            participant_role = self.guild.get_role(roles['participant'])
            institution_role = self.guild.get_role(roles[participant.institution.lower()])
            self.log.info(f"fsm.sync_server_roles: Participant\n"
                          f"\t{[participant_role, institution_role]}")

            await self.member.add_roles(institution_role,
                                        participant_role,
                                        reason='InfoChallengeConcierge added roles')
        else:
            self.log.info(f"fsm.sync_server_roles: {participant.role}\n"
                          f"\troles: {roles[participant.role.lower()]}")
            role = self.guild.get_role(roles[participant.role.lower()])
            await self.member.add_roles(role, reason='InfoChallengeConcierge added roles')


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

            if EVENT_GUILD_ID in shared_guild_ids:
                guild = [g for g in message.author.mutual_guilds if g.id == EVENT_GUILD_ID].pop()
                member = guild.get_member(message.author.id)
                reg_fsm = RegistratorConvoFSM(self.log, Session(), guild, member)

                msg, view = reg_fsm.exec(message=message.content)
                await message.reply(msg, view=view)
                if reg_fsm.state.state == 'registered':
                    await reg_fsm.sync_server_roles()
            else:
                await message.reply(
                    f"I'm sorry. We don't share any servers, so I don't know how to help you."
                )

    @commands.guild_only()
    @is_in_guild(EVENT_GUILD_ID)
    @is_in_channel(EVENT_BOT_CHANNEL_ID)
    @commands.create_group(name="register", guild_ids=[EVENT_GUILD_ID],
                           description="Commands for handling user registrations")
    async def register(self, ctx):
        await ctx.respond(f"{ctx.author.name} said...")

    @commands.guild_only()
    @is_in_guild(EVENT_GUILD_ID)
    @is_in_channel(EVENT_BOT_CHANNEL_ID)
    @register.slash_command(name="reset_me", guild_ids=[EVENT_GUILD_ID], description="Reset your roles for testing.")
    async def _reset_me(self, ctx):
        await self._reset_user_conversation(ctx, member=ctx.author)
        await ctx.respond(f"Reset roles for {ctx.author.name}.")

    @commands.guild_only()
    @is_in_guild(EVENT_GUILD_ID)
    @is_in_channel(EVENT_BOT_CHANNEL_ID)
    @register.slash_command(name="reset_user", guids_ids=[EVENT_GUILD_ID], description="Reset a users\'s roles.")
    async def _reset_user_conversation(self, ctx, member: discord.Member):
        self.log.info(f"reset_user_conversation [{member.display_name}]")
        guild = ctx.guild
        session = Session()
        participant = session.query(Participant). \
            filter(Participant.guild_id == guild.id,
                   Participant.discord_id == member.id).one_or_none()
        if participant is not None:
            roles = dict([(r.name.lower(), int(r.id)) for r in guild.roles])
            if participant.role.lower() == 'participant':
                participant_role = guild.get_role(roles['participant'])
                institution_role = guild.get_role(roles[participant.institution.lower()])
                await member.remove_roles(participant_role,
                                          institution_role,
                                          reason=f"InfoChallengeConcierge: {ctx.author.name} reset user roles")
            else:
                role = guild.get_role(roles[participant.role.lower()])
                await member.remove_roles(role, reason=f"InfoChallengeConcierge: {ctx.author.name} reset user roles")

            session.query(ConvoState).filter(ConvoState.conversation == 'registration',
                                             ConvoState.guild_id == participant.guild_id,
                                             ConvoState.discord_id == participant.discord_id).delete()
            session.delete(participant)
            session.commit()
        else:
            ctx.respond(f"User")

    @_reset_user_conversation.error
    async def _reset_user_conversation_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            self.log.info(f"Error _reset_user_error: {error}")
            await ctx.send(f"ERROR: Could not find user")
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"Error _reset_user_error: {error}")


def setup(bot):
    bot.add_cog(Registrator(bot))
