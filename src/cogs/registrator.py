import os
import discord as discord
from discord.ext import commands
from discord.ui import View, Button
from discord import ButtonStyle
from discord.commands import Option, SlashCommandGroup, CommandPermission

from validate_email_address import validate_email

import models
from models import Session, Registration, ConvoState, Participant

from common import logging, checks

from dotenv import load_dotenv

load_dotenv()

EVENT_NAME = os.getenv('event_name')
EVENT_GUILD_ID = int(os.getenv('event_guild_id'))
EVENT_CONTACT_EMAIL = os.getenv('event_contact_email')
EVENT_BOT_CHANNEL_ID = int(os.getenv('event_bot_channel_id'))
BOT_MANAGER_ROLE_ID = int(os.getenv('bot_manager_role_id'))
GUILD_OWNER_ID = int(os.getenv('guild_owner_id'))

IS_PRODUCTION = os.getenv('is_production')
LOGGING_STR = os.getenv('logging_str')


async def sync_server_roles(guild: discord.Guild, member: discord.Member, participant: models.Participant):
    # Add Discord Roles.
    roles = dict([(r.name.lower(), int(r.id)) for r in guild.roles if not r.name.lower().startswith('team ')])

    if participant.role.lower() == 'participant':
        participant_role = guild.get_role(roles['participant'])
        institution_role = guild.get_role(roles[participant.institution.lower()])

        await member.add_roles(institution_role,
                               participant_role,
                               reason='InfoChallengeConcierge added roles')
    else:
        role = guild.get_role(roles[participant.role.lower()])
        await member.add_roles(role, reason='InfoChallengeConcierge added roles')


class Confirm(View):
    def __init__(self, convo):
        super().__init__()
        self.convo = convo

    @discord.ui.button(label="Yes", emoji="✔", style=ButtonStyle.green)
    async def yes(self, button: Button, interaction: discord.Interaction):
        msg, view = self.convo.exec(message="yes")

        # this is a gross place for this to be...
        if self.convo.state.state == 'registered':
            with Session() as session:
                participant = session.query(Participant).\
                    filter(Participant.discord_id == self.convo.member.id,
                           Participant.guild_id == self.convo.guild.id).one_or_none()
                if participant is not None:
                    self.convo.log.info(f"registration confirmed: syncing server roles")
                    await sync_server_roles(self.convo.guild, self.convo.member, participant)

        # Apparently pycord doesn't like view to be present and none...
        if view is not None:
            await interaction.response.send_message(msg, view=view)
        else:
            await interaction.response.send_message(msg)

        self.stop()

    @discord.ui.button(label="No", emoji="❌", style=ButtonStyle.grey)
    async def no(self, button: Button, interaction: discord.Interaction):
        msg, view = self.convo.exec(message="no")

        # Apparently pycord doesn't like view to be present and none...
        if view is not None:
            await interaction.response.send_message(msg, view=view)
        else:
            await interaction.response.send_message(msg)

        self.stop()


# Finite State Machine "model" of a registration conversation
class RegistratorConvoFSM:
    _state: ConvoState
    member: discord.Member
    guild: discord.Guild
    conversation: str = 'registration'
    _state_funcs = ['initiate', 'email', 'confirm', 'registered']

    def __init__(self, log, guild, member):
        self.log = log
        self.member = member
        self.guild = guild
        self._resume_state()

    def _resume_state(self):
        with Session() as session:
            state_obj = session.query(ConvoState). \
                filter(ConvoState.discord_id == self.member.id,
                       ConvoState.guild_id == self.guild.id,
                       ConvoState.conversation == self.conversation).one_or_none()

            if state_obj is None:
                session.add(ConvoState(discord_id=self.member.id,
                                       guild_id=self.guild.id,
                                       conversation=self.conversation,
                                       state='initiate'))
                session.commit()
                state_obj = session.query(ConvoState). \
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
        with Session() as session:
            session.query(ConvoState). \
                filter(ConvoState.id == self.state.id). \
                update({'email': email})
            session.commit()
        self.state.email = email

    def set_state(self, state):
        self.log.info(f"fsm.set_state: {state}")
        self.state.state = state
        with Session() as session:
            session.query(ConvoState). \
                filter(ConvoState.id == self.state.id). \
                update({'state': state})
            session.commit()

    def _initiate(self, **kwargs):
        self.log.info(f"fsm._initiate: {kwargs} | id: {self.member.id}")
        self.next_state()
        response = f"Hello {self.member.name}, let me help connect your registration to this Discord server.\n" \
                   f"What is the email address you used to register for {EVENT_NAME}?"
        return response, None

    def _email(self, **kwargs):
        self.log.info(f"fsm._email: {kwargs}")
        response = "_email: No message?"
        view = None
        if 'message' in kwargs:
            email = str(kwargs['message']).lower().strip()
            if validate_email(email):
                self.log.info(f"fsm._email: valid email {email}")
                with Session() as session:
                    reg_obj = session.query(Registration). \
                        filter(Registration.email == email,
                               Registration.guild_id == self.guild.id).one_or_none()
                    if reg_obj is None:
                        self.log.info(f"fsm._email: unrecognized {email}")
                        response = f"I did not recognize the email \"{email}\". " \
                                   f"Would you like to try again? (Click on your response)"

                        view = Confirm(self)

                        self.set_state('unrecognized')
                    else:

                        part_obj = session.query(Participant). \
                            filter(Participant.email == email,
                                   Participant.guild_id == self.guild.id).one_or_none()

                        if part_obj is None or part_obj.discord_id == self.member.id:
                            self.log.info(f"fsm._email: recognized {email}")
                            response = f"I have found a registration for {reg_obj.full_name}.\n" \
                                       f"Is this correct? (Click on your response)\n"

                            view = Confirm(self)

                            self.set_state_email(email)
                            self.next_state()
                        else:
                            self.log.info(f"fsm._email: Duplicate email {email}")

                            self.set_state('unknown')
                            response, view = self.exec(**kwargs)
            else:
                self.log.info(f"fsm._email: invalid email {email}")
                response = f"Hello, {self.member.name}.\n" \
                           f"What is the email address you used to register for {EVENT_NAME}?"
        return response, view

    def _unrecognized(self, **kwargs):
        self.log.info(f"fsm._unrecognized: {kwargs}")
        response = "_unrecognized: No message?"
        view = None
        if 'message' in kwargs:
            message = str(kwargs['message']).strip().lower()
            if message == 'yes':
                response = f"Please reply with the email address you used to register for {EVENT_NAME}."
                self.set_state('email')
            elif message == 'no':
                self.set_state('unknown')
                response, view = self.exec(**kwargs)
            else:
                response = f"I'm sorry. I didn't understand your response.\n" \
                           f"Would you like to try another email address? (Click on your response)"

                view = Confirm(self)
        return response, view

    def _confirm(self, **kwargs):
        self.log.info(f"fsm._confirm: {kwargs}")
        response = '_confirm: No message?'
        view = None
        if 'message' in kwargs:
            with Session() as session:
                reg_obj = session.query(Registration). \
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
                        response = f"Would you like to try another email address? (Click on your response)"
                        view = Confirm(self)
                        self.set_state('unrecognized')
                    else:
                        response = f"I'm sorry, I didn't understand your response.\n" \
                                   f"Are you {reg_obj.full_name}?\n" \
                                   f"(Click on your response)\n"
                        view = Confirm(self)
        return response, view

    def _registered(self, **kwargs):
        self.log.info(f"fsm._registered: {kwargs}")
        with Session() as session:
            reg_obj = session.query(Registration). \
                filter(Registration.email == self.state.email,
                       Registration.guild_id == self.guild.id).one_or_none()

            view = None
            if reg_obj is None:
                self.set_state('unknown')
                response, view = self.exec(**kwargs)
            else:
                participant = session.query(Participant). \
                    filter(Participant.guild_id == self.guild.id,
                           Participant.discord_id == self.member.id).one_or_none()
                if participant is None:
                    session.add(Participant(discord_id=self.member.id,
                                            guild_id=self.guild.id,
                                            email=reg_obj.email,
                                            institution=reg_obj.institution,
                                            role=reg_obj.role))
                    session.commit()

            response = f"{self.member.name}, your registration is now complete. Congratulations!\n" \
                       f"You will now have access to the participate in the {EVENT_NAME} Discord."
        return response, view

    def _unknown(self, **kwargs):
        self.log.info(f"fsm._unknown: {self.member.id} - {self.member.name}")
        response = f"{self.member.name}, please email {EVENT_CONTACT_EMAIL} for support."
        return response, None


class Registrator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.get_module_logger(LOGGING_STR)
        self.log.info(f"Booting up Cog: Registrations")

    registrator_group = SlashCommandGroup(
        "reg",
        "Commands to manage registrations",
        guild_ids=[EVENT_GUILD_ID],
        permissions=[
            CommandPermission(
                BOT_MANAGER_ROLE_ID, 1, True
            ),  # Only Users in Discord Managers
            CommandPermission(
                GUILD_OWNER_ID, 2, True
            ),  # Always allow owner
        ]
    )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot is True:
            return

        if member.guild.id == EVENT_GUILD_ID:
            reg_fsm = RegistratorConvoFSM(self.log, member.guild, member)
            msg, view = reg_fsm.exec()
            await member.send(msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.command_prefix):
            return
        # Only respond to direct messages (messages without a guild)
        if not message.guild:
            shared_guild_ids = [g.id for g in message.author.mutual_guilds]

            if EVENT_GUILD_ID in shared_guild_ids:
                guild = [g for g in message.author.mutual_guilds if g.id == EVENT_GUILD_ID].pop()
                member = guild.get_member(message.author.id)
                reg_fsm = RegistratorConvoFSM(self.log, guild, member)
                msg, view = reg_fsm.exec(message=message.content)

                # Pycord does not like it if there is a view argument that is set to none...
                if view is not None:
                    await message.reply(msg, view=view)
                else:
                    await message.reply(msg)

            else:
                await message.reply(
                    f"I'm sorry. We don't share any servers, so I don't know how to help you."
                )

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @registrator_group.command(name="reset", description="🚫 [RESTRICTED] Reset a users\'s roles.")
    async def _reset_user(self, ctx,
                          member: Option(discord.Member,
                                         "Optional: User to reset [Default: Self]",
                                         required=False,
                                         default=None)):
        if member is None:
            member = ctx.author

        self.log.info(f"reset_user_conversation [{member.display_name}]")
        guild = ctx.guild
        with Session() as session:
            participant = session.query(Participant). \
                filter(Participant.guild_id == guild.id,
                       Participant.discord_id == member.id).one_or_none()

            del_cnt = session.query(ConvoState).filter(ConvoState.conversation == 'registration',
                                                       ConvoState.guild_id == guild.id,
                                                       ConvoState.discord_id == member.id).delete()
            session.commit()
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
                    await member.remove_roles(role,
                                              reason=f"InfoChallengeConcierge: {ctx.author.name} reset user roles")

                session.delete(participant)
                session.commit()
                await ctx.respond(f"**`SUCCESS:`** Reset user [{member.display_name}]", ephemeral=True)
            else:
                if del_cnt > 0:
                    await ctx.respond(f"**`SUCCESS:`** Reset user [{member.display_name}].", ephemeral=True)
                else:
                    await ctx.respond(f"**`ERROR:`** User [{member.display_name}] was not registered.", ephemeral=True)

    @_reset_user.error
    async def _reset_user_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            self.log.info(f"**`ERROR:`** _reset_user_error[{ctx.author.name}]: {error}")
            await ctx.send(f"**`ERROR:`** Could not find user", ephemeral=True)
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"**`ERROR:`** _reset_user_error[{ctx.author.name}]: {error}")

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @registrator_group.command(name="connect_account", description="🚫 [RESTRICTED] Register a user.")
    async def _add_participant(self, ctx,
                               member: Option(discord.Member,
                                              "Required: User to reset",
                                              required=True),
                               email: Option(str, "Required: The user's email address.", required=True)):

        self.log.info(f"Connecting registration for participant [{member.display_name}]")
        guild = ctx.guild
        with Session() as session:
            registration = session.query(Registration). \
                filter(Registration.guild_id == guild.id,
                       Registration.email == email).one_or_none()

            session.commit()
            if registration is not None:
                participant = Participant(discord_id=member.id,
                                          guild_id=guild.id,
                                          email=registration.email,
                                          institution=registration.institution,
                                          role=registration.role)
                session.add(participant)

                session.query(ConvoState).filter(ConvoState.discord_id == member.id,
                                                 ConvoState.guild_id == guild.id).delete()
                session.add(ConvoState(discord_id=member.id,
                                       guild_id=guild.id,
                                       conversation='registration',
                                       state='registered'))
                session.commit()
                session.refresh(participant)
                await sync_server_roles(guild, member, participant)

                await ctx.respond(f"**`SUCCESS:`** Connected registration for user [{member.display_name}]",
                                  ephemeral=True)
            else:
                await ctx.respond(f"**`ERROR:`** User [{member.display_name}] was not registered.", ephemeral=True)

    @_add_participant.error
    async def _add_participant_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            self.log.info(f"**`ERROR:`** _add_participant_error[{ctx.author.name}]: {error}")
            await ctx.send(f"**`ERROR:`** Could not find user", ephemeral=True)
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"**`ERROR:`** _add_participant_error[{ctx.author.name}]: {error}")

    @commands.guild_only()
    @registrator_group.command(name='member_by_email', description="🚫 [RESTRICTED] Debug information.")
    async def _member_by_email(self, ctx,
                               email: Option(str,
                                             "Optional: Email of the member to lookup.",
                                             required=True)):
        with Session() as session:
            participant = session.query(Participant). \
                filter(Participant.email == email,
                       Participant.guild_id == ctx.guild.id).one_or_none()

            if participant is not None:
                member = ctx.guild.get_member(participant.discord_id)
                if member is not None:
                    response = f"User Info for {email}:\n" \
                               f"\tMember Name: {member.name}\n" \
                               f"\tMember Nick: {member.nick}\n" \
                               f"\tCreated At: {member.created_at}\n" \
                               f"\tJoined At: {member.joined_at}\n" \
                               f"\tMember ID: {member.id}\n" \
                               f"\tNumber of Roles: {len(member.roles)}\n" \
                               f"\tTop Role: {member.top_role.name}"
                else:
                    response = f"No member for id {participant.discord_id}. Maybe they left the server?"
            else:
                response = f"No participant found for {email}"
        await ctx.respond(response, ephemeral=True)

    @_member_by_email.error
    async def _member_by_email_error(self, ctx, error):
        self.log.info(f"**`ERROR:`** Test[{ctx.author.name}]: {type(error).__name__} - {error}")

    @commands.guild_only()
    @registrator_group.command(name='hard_fix_perms', description="🚫 [RESTRICTED] Debug information.")
    async def _hard_fix_perms(self, ctx):
        with Session() as session:
            participants = session.query(Participant). \
                filter(Participant.guild_id == ctx.guild.id).all()
            self.log.info(f"_hard_fix_perms: {len(participants)} participants")
            await ctx.respond(f"Hard fixing permissions for {len(participants)} participants", ephemeral=True)
            for participant in participants:
                member = ctx.guild.get_member(participant.discord_id)
                if member is not None:
                    self.log.info(f"_hard_fix_perms: name: {member.display_name} id: {member.id} num_roles: {len(member.roles)}"
                                  f" top_role: {member.top_role.name}")

                    await sync_server_roles(ctx.guild, member, participant)
            await ctx.respond(f"Hard fixing permissions: Complete", ephemeral=True)
            self.log.info(f"_hard_fix_perms: complete")

    @_hard_fix_perms.error
    async def _fix_perms_error(self, ctx, error):
        self.log.info(f"**`ERROR:`** _hard_fix_perms[{ctx.author.name}]: {type(error).__name__} - {error}")


def setup(bot):
    bot.add_cog(Registrator(bot))
