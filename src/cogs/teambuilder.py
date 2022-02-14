import os
import re

import discord as discord
from discord.commands import CommandPermission, Option, SlashCommandGroup
from discord.ext import commands
from dotenv import load_dotenv

from common import checks, logging
from models import Participant, Session, Team, TeamRegistration, TeamParticipant

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
                                            permissions=perms)
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
        with Session() as session:
            num_teams = session.query(TeamRegistration). \
                filter(TeamRegistration.guild_id == ctx.guild.id). \
                group_by(TeamRegistration.team_name). \
                count()

            await ctx.respond(f"**`START:`** _build_teams: Building {num_teams} Teams", ephemeral=True)
            self.log.info(f"**`START:`** _build_teams: {ctx.author.name} is building {num_teams} teams.")

            team_reg_participants = session.query(TeamRegistration, Participant). \
                filter(TeamRegistration.guild_id == ctx.guild.id,
                       TeamRegistration.email == Participant.email,
                       TeamRegistration.guild_id == Participant.guild_id). \
                order_by(TeamRegistration.team_name). \
                all()

            # Empty Team to start because None doesn't work
            cur_team = None
            for team_registration, participant in team_reg_participants:
                # if a new team, make one and set it to cur_team
                if cur_team is None or cur_team.team_name != team_registration.team_name:
                    team = session.query(Team). \
                        filter(Team.team_name == team_registration.team_name,
                               Team.guild_id == ctx.guild.id). \
                        one_or_none()
                    if team is None:
                        await ctx.respond(f"Creating Team: {team_registration.team_name}", ephemeral=True)
                        team = await self._create_team(session, team_registration.team_name, ctx.guild)
                    cur_team = team

                # Check if participant is in a team. If in team, then skip.
                team_participant = session.query(TeamParticipant). \
                    filter(TeamParticipant.team_id == cur_team.id,
                           TeamParticipant.participant_id == participant.id,
                           TeamParticipant.guild_id == ctx.guild.id). \
                    one_or_none()
                if team_participant is None:
                    # Update database to show that the participant is in a team.
                    team_participant = TeamParticipant(
                        team_id=cur_team.id,
                        participant_id=participant.id,
                        guild_id=ctx.guild.id
                    )
                    session.add(team_participant)
                    session.commit()
                # add member to team role if they don't have it yet
                guild_member = ctx.guild.get_member(participant.discord_id)
                if guild_member.get_role(cur_team.team_role_id) is None:
                    team_role = ctx.guild.get_role(cur_team.team_role_id)
                    await guild_member.add_roles(team_role, reason="Team registration")

        await ctx.respond(f"**`SUCCESS:`** _build_teams: Created {num_teams} teams.", ephemeral=True)
        self.log.info(f"**`SUCCESS:`** _build_teams: {ctx.author.name} created {num_teams} teams.")

    @_build_teams.error
    async def _build_teams_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.respond(f"**`ERROR:`** _build_teams[{ctx.author.name}]: {error}")
            self.log.info(f"**`ERROR:`** _build_teams[{ctx.author.name}]: {error}")

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @tb_group.command(name="delete", description="🚫 [RESTRICTED] Delete participant teams")
    async def _delete(self, ctx, num: Option(int, "Number to delete [Default: 1]", required=False, default=1)):
        self.log.info(f"{ctx.author.name} called '/teams delete num:{num}'")
        guild = ctx.guild

        tnm = re.compile('^Team ([0-9]+)')
        categories = dict(
            [(int(tnm.match(c.name).group(1)), c) for c in guild.categories if tnm.match(c.name) is not None])
        category_index = list(categories.keys())
        category_index.sort(reverse=True)

        self.log.info(f"Team category IDs: {category_index}")

        team_roles = dict([(int(tnm.match(r.name).group(1)), r) for r in guild.roles if tnm.match(r.name) is not None])
        self.log.info(f"Team role IDs: {team_roles}")

        cnt = 0
        if num >= len(category_index):
            cats_to_iter = category_index
        else:
            cats_to_iter = category_index[:num]

        await ctx.respond(f"Deleting {len(cats_to_iter)} teams.", ephemeral=True)

        with Session() as session:
            for n in cats_to_iter:
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

    @_delete.error
    async def _old_delete_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"**`ERROR:`** _delete_teams[{ctx.author.name}]: {error}")


def setup(bot):
    bot.add_cog(TeamBuilder(bot))
