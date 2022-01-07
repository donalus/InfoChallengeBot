import os
import re
import discord as discord
from discord.ext import commands
from discord.ui import View, Button
from discord.commands import permissions, Option, SlashCommandGroup, CommandPermission

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


class TeamBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.get_module_logger(LOGGING_STR)
        self.log.info(f"Booting up Cog: TeamBuilder")

    tb_group = SlashCommandGroup(
        "teams",
        "Commands to manage teams",
        guild_ids=[EVENT_GUILD_ID]
    )

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @permissions.has_role("Discord Managers")
    @tb_group.command(name="create", description="🚫 [RESTRICTED] Add participant teams",
                      permissions=[CommandPermission(GUILD_OWNER_ID, 2, True)])
    async def _create(self, ctx, num: Option(int, "Number to create [Default: 1]", required=False, default=1)):
        guild = ctx.guild

        tnm = re.compile('^Team ([0-9]+)')
        team_cats = [int(tnm.match(c.name).group(1)) for c in guild.categories if tnm.match(c.name)]

        max_cur_team_num = 0
        if len(team_cats) > 0:
            max_cur_team_num = max(team_cats)

        await ctx.respond(f"Adding {num} teams.", ephemeral=True)

        for n in range(1, 1 + num):
            next_team_num = max_cur_team_num + n
            team_name = f"Team {next_team_num}"
            team_prefix = f"team-{next_team_num}"
            perms = discord.Permissions.none()
            new_team_role = await guild.create_role(name=team_name,
                                                    permissions=perms)
            roles = [(r.name, r) for r in guild.roles if r.name in ['Volunteer', 'DSA', 'Dataset Partner']]
            roles_dict = dict(roles)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                new_team_role: discord.PermissionOverwrite(
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
                roles_dict['DSA']: discord.PermissionOverwrite(view_channel=True),
                roles_dict['Dataset Partner']: discord.PermissionOverwrite(view_channel=True)
            }

            cat = await guild.create_category_channel(team_name, overwrites=overwrites)

            await cat.create_text_channel(f"{team_prefix}-text")
            await cat.create_voice_channel(f"{team_prefix}-voice")

        await ctx.respond(f"**`SUCCESS:`** Created {num} teams.", ephemeral=True)
        self.log.info(f"**`SUCCESS:`** _create_teams: {ctx.author.name} created {num} teams.")

    @_create.error
    async def _create_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"**`ERROR:`** _create_teams[{ctx.author.name}]: {error}")

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @permissions.has_role("Discord Managers")
    @tb_group.command(name="delete", description="🚫 [RESTRICTED] Delete participant teams",
                      permissions=[CommandPermission(GUILD_OWNER_ID, 2, True)])
    async def _delete(self, ctx, num: Option(int, "Number to delete [Default: 1]", required=False, default=1)):
        self.log.info(f"{ctx.author.name} called '/teams delete num:{num}'")
        guild = ctx.guild

        tnm = re.compile('^Team ([0-9]+)')
        categories = dict([(int(tnm.match(c.name).group(1)), c) for c in guild.categories if tnm.match(c.name)])
        category_index = list(categories.keys())
        category_index.sort(reverse=True)

        self.log.info(f"Team category IDs: {category_index}")

        team_roles = dict([(int(tnm.match(r.name).group(1)), r) for r in guild.roles if tnm.match(r.name)])
        self.log.info(f"Team role IDs: {team_roles}")

        cnt = 0
        if num >= len(category_index):
            cats_to_iter = category_index
        else:
            cats_to_iter = category_index[:num]

        await ctx.respond(f"Deleting {len(cats_to_iter)} teams.", ephemeral=True)

        for n in cats_to_iter:
            cat = categories[n]

            for sub_channel in cat.channels:
                self.log.info(f"Deleting category channel: {sub_channel.name}")
                await sub_channel.delete()

            self.log.info(f"Deleting category: {cat.name}")
            await cat.delete()

            role = team_roles.get(n)
            if role is not None:
                self.log.info(f"Deleting role: {role.name}")
                await role.delete()

            cnt = cnt + 1

        await ctx.respond(f"**`SUCCESS:`** Deleted {cnt} teams.", ephemeral=True)
        self.log.info(f"**`SUCCESS:`** _delete_teams: {ctx.author.name} deleted {cnt} teams.")

    @_delete.error
    async def _delete_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"**`ERROR:`** _delete_teams[{ctx.author.name}]: {error}")


def setup(bot):
    bot.add_cog(TeamBuilder(bot))
