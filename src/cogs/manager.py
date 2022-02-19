import os

import discord as discord
from discord.commands import permissions, Option, SlashCommandGroup, CommandPermission
from discord.ext import commands
from dotenv import load_dotenv

from common import logging, checks

load_dotenv()

LOGGING_STR = os.getenv('logging_str')
EVENT_GUILD_ID = int(os.getenv('event_guild_id'))
EVENT_BOT_CHANNEL_ID = int(os.getenv('event_bot_channel_id'))
BOT_MANAGER_ROLE_ID = int(os.getenv('bot_manager_role_id'))
GUILD_OWNER_ID = int(os.getenv('guild_owner_id'))


class Manager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.get_module_logger(LOGGING_STR)
        self.log.info(f"Booting up Cog: Registrations")

    manager_group = SlashCommandGroup(
        "manager",
        "Commands to manage InfoChallengeConcierge",
        guild_ids=[EVENT_GUILD_ID],
        permissions=[
            CommandPermission(
                BOT_MANAGER_ROLE_ID, 1, True
            ),  # Only Users in Discord Managers
            CommandPermission(
                GUILD_OWNER_ID, 2, True
            )  # Ensures the owner_id user can access this, and no one else
        ]
    )

    @commands.guild_only()
    @manager_group.command(name='user_info', description="🚫 [RESTRICTED] Debug information.")
    async def _user_info(self, ctx,
                         member: Option(discord.Member,
                                        "Optional: The user to display info on.",
                                        required=False,
                                        default=None),
                         discord_id: Option(str,
                                            required=False,
                                            default=None)):
        response = f"No member or discord_id sent"
        if discord_id is not None and discord_id.isnumeric():
            member = ctx.guild.get_member(int(discord_id))
        if member is not None:
            response = f"User Info:\n" \
                       f"\tMember Name: {member.name}\n" \
                       f"\tMember Nick: {member.nick}\n" \
                       f"\tCreated At: {member.created_at}\n" \
                       f"\tJoined At: {member.joined_at}\n" \
                       f"\tMember ID: {member.id}\n" \
                       f"\tNumber of Roles: {len(member.roles)}\n" \
                       f"\tTop Role: {member.top_role.name}"
        await ctx.respond(response, ephemeral=True)

    @_user_info.error
    async def _user_info_error(self, ctx, error):
        self.log.info(f"**`ERROR:`** Test[{ctx.author.name}]: {type(error).__name__} - {error}")

    @commands.guild_only()
    @manager_group.command(name='debug', description="🚫 [RESTRICTED] Debug information.")
    async def _debug(self, ctx):
        is_owner = await self.bot.is_owner(ctx.author)

        guild = ctx.guild
        roles = guild.roles
        bot_manager_role = [r for r in roles if r.name == 'Planning Team'].pop()

        response = f"Debug info:\n" \
                   f"\tGuild ID: {ctx.guild.id}\n" \
                   f"\tGuild Name: {ctx.guild.name}\n" \
                   f"\tChannel ID: {ctx.channel.id}\n" \
                   f"\tChannel Name: {ctx.channel.name}\n" \
                   f"\tMember ID: {ctx.author.id}\n" \
                   f"\tMember Name: {ctx.author.name}\n" \
                   f"\tIs Owner: {is_owner}\n" \
                   f"\tTeam Role ID: {bot_manager_role.id}"
        self.log.info(response)
        await ctx.respond(response, ephemeral=True)

    @_debug.error
    async def _debug_error(self, ctx, error):
        self.log.info(f"**`ERROR:`** Test[{ctx.author.name}]: {type(error).__name__} - {error}")

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @permissions.is_owner()
    @manager_group.command(name='unload_cog', description="🚫 [RESTRICTED] Unload cog")
    async def _unload_cog(self, ctx, *, cog: Option(str, "What cog do you want to unload?")):
        self.log.info(f"unload_cog [cogs.{cog}] of {len(self.bot.extensions)}: {ctx.author.name}")

        if cog != "manager":
            try:
                self.bot.unload_extension(f"cogs.{cog}")
            except Exception as e:
                self.log.info(f"ERROR: unload_cog [cogs.{cog}]:{type(e).__name__}")
                await ctx.respond(f"**`ERROR:`** {type(e).__name__} - {e}", ephemeral=True)
            else:
                self.log.info(f"unload_cog [cogs.{cog}] of {len(self.bot.extensions)}: SUCCESS")
                await ctx.respond(f"**`SUCCESS`** {cog} Unloaded", ephemeral=True)
        else:
            await ctx.respond(f"**`ERROR:`** Cannot Unload Manager Cog", ephemeral=True)

    @_unload_cog.error
    async def _unload_cog_error(self, ctx, error):
        self.log.info(f"**`ERROR:`** Unload Cog[{ctx.author.name}]: {type(error).__name__} - {error}")

    @commands.guild_only()
    @checks.is_in_channel(EVENT_BOT_CHANNEL_ID)
    @permissions.is_owner()
    @manager_group.command(name='load_cog', description="🚫 [RESTRICTED] Load cog")
    async def _load_cog(self, ctx, *, cog: Option(str, "What cog do you want to load?")):
        self.log.info(f"load_cog [cogs.{cog}] of {len(self.bot.extensions)}: {ctx.author.name}")
        try:
            self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            self.log.info(f"ERROR: load_cog [cogs.{cog}]:{type(e).__name__}")
            await ctx.respond(f"**`ERROR:`** {type(e).__name__} - {e}", ephemeral=True)
        else:
            self.log.info(f"load_cog [cogs.{cog}] of {len(self.bot.extensions)}: SUCCESS")
            await ctx.respond(f"**`SUCCESS`** {cog} Loaded", ephemeral=True)

    @_load_cog.error
    async def _unload_cog_error(self, ctx, error):
        self.log.info(f"**`ERROR:`** Load Cog[{ctx.author.name}]: {type(error).__name__} - {error}")

    @commands.guild_only()
    @manager_group.command(name='purge', description="🚫 [RESTRICTED] Purge messages from a channel")
    async def _purge(self, ctx,
                     channel: Option(discord.TextChannel, "Which channel do you want to purge? [Default: Current]",
                                     required=False,
                                     default=None),
                     limit: Option(int, "Optional: number of messages to remove. [Default: 10]",
                                   required=False,
                                   default=10),
                     user: Option(discord.Member, "Optional: remove messages by specified user.",
                                  required=False,
                                  default=None)):
        if channel is None:
            channel = ctx.channel
        if user is not None:
            deleted = await channel.purge(limit=limit, check=lambda m: m.author == user)
        else:
            deleted = await channel.purge(limit=limit)
        await ctx.respond(f"{ctx.author.name} purged {channel.name} of {len(deleted)} messages.", ephemeral=True)
        self.log.info(f"{ctx.author.name} purged {channel.name} of {len(deleted)} messages.")


def setup(bot):
    bot.add_cog(Manager(bot))
