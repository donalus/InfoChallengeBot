import os
import re
import time

import discord
from discord.commands import Option, CommandPermission, SlashCommandGroup
from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy import select, delete

from common import checks, logging
from models import Participant, Session, Team, TeamRegistration, TeamParticipant, Registration

load_dotenv()

EVENT_NAME = os.getenv('event_name')
EVENT_GUILD_ID = int(os.getenv('event_guild_id'))
EVENT_CONTACT_EMAIL = os.getenv('event_contact_email')
EVENT_BOT_CHANNEL_ID = int(os.getenv('event_bot_channel_id'))
BOT_MANAGER_ROLE_ID = int(os.getenv('bot_manager_role_id'))
GUILD_OWNER_ID = int(os.getenv('guild_owner_id'))

IS_PRODUCTION = os.getenv('is_production')
LOGGING_STR = os.getenv('logging_str')


def _filter_team_cats(guild):
    tnm = re.compile('^Team ([0-9]+)')
    team_cats = [int(tnm.match(c.name).group(1)) for c in guild.categories if tnm.match(c.name) is not None]
    return team_cats


def _get_team_cat_and_role(guild, team_name):
    categories = dict(
        [(c.name, c) for c in guild.categories if c.name.lower().startswith('team ')])
    roles = dict([(r.name, r) for r in guild.roles if r.name.lower().startswith('team ')])

    team_cat = None
    if team_name in categories.keys():
        team_cat = categories[team_name]

    team_role = None
    if team_name in roles.keys():
        team_role = roles[team_name]

    return team_cat, team_role


class TeamBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.get_module_logger(LOGGING_STR)
        self.log.info(f"Booting up Cog: TeamBuilder")

    tb_group = SlashCommandGroup(
        "teams",
        "Commands to manage teams",
        guild_ids=[EVENT_GUILD_ID],
        permissions=[
            CommandPermission(
                GUILD_OWNER_ID, 2, True
            ),  # Always allow owner
        ]
    )

    async def _create_team(self, session, team_name, guild: discord.Guild):
        perms = discord.Permissions.none()

        team_role = await guild.create_role(name=team_name,
                                            permissions=perms,
                                            hoist=True)
        team = Team(team_name=team_name,
                    guild_id=guild.id,
                    team_role_id=team_role.id)
        session.add(team)
        session.commit()

        roles = [(r.name, r) for r in guild.roles if r.name in ['Volunteer', 'IC Advisor', 'Project Partner']]
        roles_dict = dict(roles)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            team_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                send_messages_in_threads=True,
                create_public_threads=True,
                create_private_threads=False,
                read_messages=True,
                read_message_history=True,
                embed_links=True,
                attach_files=True,
                add_reactions=True,
                mention_everyone=True,
                connect=True,
                speak=True,
                stream=True,
                use_voice_activation=True,
            ),
            roles_dict['Volunteer']: discord.PermissionOverwrite(view_channel=True),
            roles_dict['IC Advisor']: discord.PermissionOverwrite(view_channel=True),
            roles_dict['Project Partner']: discord.PermissionOverwrite(view_channel=True)
        }

        cat = await guild.create_category_channel(team_name, overwrites=overwrites)

        chan_prefix = team_name.strip().replace(' ', '-').lower()
        await cat.create_text_channel(f"{chan_prefix}-text")
        await cat.create_voice_channel(f"{chan_prefix}-voice")
        self.log.info(f"Created team {team_name}")
        return team

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @tb_group.command(name="build", description="🚫 [RESTRICTED] Build teams from team registrations")
    async def _build_teams(self, ctx):
        await ctx.respond(f"**`START:`** _build_teams")
        self.log.info(f"**`START:`** _build_teams")
        with Session() as session:
            stmt = select(TeamRegistration.team_name). \
                where(TeamRegistration.guild_id == ctx.guild.id). \
                distinct(). \
                order_by(TeamRegistration.team_name)

            team_names_result = session.execute(stmt).columns(TeamRegistration.team_name).all()

            await ctx.respond(f"_build_teams: Building {len(team_names_result)} Teams", ephemeral=True)
            self.log.info(f"_build_teams: {ctx.author.name} is building {len(team_names_result)} teams.")

            cur_team = ''
            num_teams_created = 0
            for t in team_names_result:
                # enforce format
                if not t.team_name.startswith('Team '):
                    team_name = f"Team {t.team_name}"
                else:
                    team_name = t.team_name

                # if a new team, then make one
                team = session.query(Team). \
                    filter(Team.team_name == team_name,
                           Team.guild_id == ctx.guild.id). \
                    one_or_none()

                if team is None:
                    await ctx.respond(f"_build_teams: Creating Team: {team_name}", ephemeral=True)
                    team = await self._create_team(session, team_name, ctx.guild)
                    num_teams_created += 1

                if cur_team != team.team_name:
                    self.log.info(f"_build_teams: Adding members to {team.team_name}")
                    await ctx.respond(f"_build_teams: Adding members to {team.team_name}")
                    cur_team = team.team_name

                team_reg_participants = session.query(TeamRegistration, Participant). \
                    filter(TeamRegistration.guild_id == ctx.guild.id,
                           TeamRegistration.email == Participant.email,
                           TeamRegistration.guild_id == Participant.guild_id,
                           TeamRegistration.team_name == t.team_name). \
                    all()

                self.log.info(f"_build_teams: {team.team_name} has {len(team_reg_participants)} members.")
                cnt = 0
                for team_registration, participant in team_reg_participants:
                    self.log.info(f"_build_teams: {team.team_name} member {cnt} is {participant.discord_id}.")
                    # add member to team role
                    guild_member = ctx.guild.get_member(participant.discord_id)
                    self.log.info(f"_build_teams: {guild_member is not None}")
                    if guild_member is not None:
                        self.log.info(f"_build_teams: {participant.discord_id} is {guild_member}")

                        await ctx.respond(f"_build_teams: Adding {guild_member.display_name} to {team.team_name}",
                                          ephemeral=True)
                        # Check if participant is in a team. If in team, then skip.
                        num_teams = session.query(TeamParticipant). \
                            filter(TeamParticipant.participant_id == participant.id,
                                   TeamParticipant.guild_id == ctx.guild.id). \
                            count()

                        in_current_team = session.query(TeamParticipant). \
                            filter(TeamParticipant.participant_id == participant.id,
                                   TeamParticipant.guild_id == ctx.guild.id,
                                   TeamParticipant.team_id == team.id). \
                            count()

                        self.log.info(f"_build_teams: r={participant.role.lower()} n={num_teams} t={in_current_team}")
                        if (participant.role.lower() == 'participant' and num_teams == 0) or \
                                (participant.role.lower() != 'participant' and in_current_team == 0):
                            # Update database to show that the participant is in a team.
                            team_participant = TeamParticipant(
                                team_id=team.id,
                                participant_id=participant.id,
                                guild_id=ctx.guild.id
                            )
                            session.add(team_participant)
                            session.commit()

                            team_role = ctx.guild.get_role(team.team_role_id)
                            await guild_member.add_roles(team_role, reason="Team registration")
                    else:
                        await ctx.respond(f"_build_teams: {participant.discord_id} left server.", ephemeral=True)
                        self.log.info(f"_build_teams: {participant.discord_id} left server.")

                    cnt += 1
                # time.sleep(0.05)  # are we getting throttled?

        await ctx.respond(f"**`SUCCESS:`** _build_teams: Created {num_teams_created} teams.", ephemeral=True)
        self.log.info(f"**`SUCCESS:`** _build_teams: {ctx.author.name} created {num_teams_created} teams.")

    @_build_teams.error
    async def _build_teams_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.respond(f"**`ERROR:`** _build_teams[{ctx.author.name}]: {error}")
            self.log.info(f"**`ERROR:`** _build_teams[{ctx.author.name}]: {error}")

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @tb_group.command(name="delete_all_teams", description="🚫 [RESTRICTED] Delete all participant teams")
    async def _delete(self, ctx,
                      confirm: Option(bool,
                                      "Required: Are you sure? [Default: False]",
                                      required=False,
                                      default=False)):
        self.log.info(f"{ctx.author.name} called '/teams delete confirm {confirm}'")
        if confirm:
            guild = ctx.guild

            tnm = re.compile('^Team IC([0-9]{5})', re.I)
            categories = dict(
                [(int(tnm.match(c.name).group(1)), c) for c in guild.categories if tnm.match(c.name) is not None])
            category_index = list(categories.keys())
            category_index.sort(reverse=True)

            self.log.info(f"Team category IDs: {category_index}")

            team_roles = dict([(int(tnm.match(r.name).group(1)), r) for r in guild.roles if tnm.match(r.name) is not None])
            self.log.info(f"Team role IDs: {team_roles}")

            await ctx.respond(f"Deleting {len(category_index)} teams.", ephemeral=True)
            cnt = 0
            with Session() as session:
                for n in category_index:
                    cat = categories[n]

                    for sub_channel in cat.channels:
                        self.log.info(f"Deleting category sub-channel: {sub_channel.name}")
                        await sub_channel.delete()

                    self.log.info(f"Deleting category: {cat.name}")
                    await cat.delete()

                    role = team_roles.get(n)
                    if role is not None:
                        self.log.info(f"Deleting role: {role.name}")
                        await role.delete()
                        team = session.query(Team). \
                            filter(Team.team_role_id == role.id). \
                            one_or_none()
                        if team is not None:
                            session.query(TeamParticipant). \
                                filter(TeamParticipant.team_id == team.id). \
                                delete()
                            session.delete(team)
                            session.commit()

                    cnt = cnt + 1

            await ctx.respond(f"**`SUCCESS:`** Deleted {cnt} teams.", ephemeral=True)
            self.log.info(f"**`SUCCESS:`** _delete_teams: {ctx.author.name} deleted {cnt} teams.")
        else:
            await ctx.respond(f"Delete called without confirmation. Nothing was deleted.", ephemeral=True)
            self.log.info(f"Delete called without confirmation. Nothing was deleted.")

    @_delete.error
    async def _delete_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"**`ERROR:`** _delete_teams[{ctx.author.name}]: {error}")

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @tb_group.command(name="delete_one", description="🚫 [RESTRICTED] Delete specified team")
    async def _delete_one(self, ctx,
                          team_name=Option(str,
                                           "Required: Email of the member to lookup.",
                                           required=True)):
        await ctx.respond(f"Deleting {team_name}", ephemeral=True)
        guild = ctx.guild
        with Session() as session:
            team = session.query(Team). \
                filter(Team.team_name == team_name,
                       Team.guild_id == guild.id). \
                one_or_none()
            if team is not None:
                team_cat, team_role = _get_team_cat_and_role(guild, team.team_name)
                if team_cat is not None:
                    for sub_channel in team_cat.channels:
                        self.log.info(f"Deleting category sub-channel: {sub_channel.name}")
                        await sub_channel.delete()

                    self.log.info(f"Deleting category: {team_cat.name}")
                    await team_cat.delete()
                if team_role is not None:
                    self.log.info(f"Deleting role: {team_role.name}")
                    await team_role.delete()

                purge_objs = session.query(TeamParticipant, Participant). \
                    filter(TeamParticipant.participant_id == Participant.id,
                           TeamParticipant.team_id == team.id). \
                    all()
                self.log.info(f"_delete_one: {len(purge_objs)}")
                for _, participant in purge_objs:
                    participant_id = participant.id
                    stmt = delete(TeamParticipant).where(TeamParticipant.participant_id == participant_id)
                    session.execute(stmt)
                    if participant.role.lower() == 'participant':

                        member = guild.get_member(participant.discord_id)
                        if member is not None:
                            self.log.info(f"Kicking participant: {member}")
                            await member.kick(reason=f"Thank you for your interest in {EVENT_NAME}. "
                                                     f"We hope to see you next year!")
                        stmt = delete(Participant).where(Participant.id == participant_id)
                        session.execute(stmt)
                        stmt = delete(Registration).where(Registration.email == participant.email,
                                                          Registration.guild_id == guild.id)
                        session.execute(stmt)
                    session.commit()
            else:
                await ctx.respond(f"No team named {team_name} was found.", ephemeral=True)
                self.log.info(f"No team named {team_name} was found.")


def setup(bot):
    bot.add_cog(TeamBuilder(bot))
