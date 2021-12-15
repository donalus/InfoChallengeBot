import logging
import os

import discord
from discord.ext import commands
from discord.commands import Option, SlashCommandGroup, Permission
from dotenv import load_dotenv

load_dotenv()

LOGGING_STR = os.getenv('logging_str')
EVENT_GUILD_ID = int(os.getenv('event_guild_id'))
EVENT_BOT_CHANNEL_ID = int(os.getenv('event_bot_channel_id'))


def is_in_channel(channel_id):
    async def predicate(ctx):
        return ctx.channel and ctx.channel.id == channel_id

    return commands.check(predicate)


class Manager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(LOGGING_STR)
        self.log.info(f"Booting up Cog: Registrations")

    manager_group = SlashCommandGroup("manager", "Commands to manage InfoChallengeConcierge")

    @commands.guild_only()
    @is_in_channel(EVENT_BOT_CHANNEL_ID)
    @manager_group.command(name="greet")
    async def _greet(self, ctx, member: Option(discord.Member, "Who do you want to greet?")):
        await ctx.respond(f"Hello {member.name}!")

    @commands.guild_only()
    @is_in_channel(EVENT_BOT_CHANNEL_ID)
    @manager_group.command(name='test')
    async def _test(self, ctx):
        is_owner = await self.bot.is_owner(ctx.author)
        response = f"Test info:\n" \
                   f"\tChannel ID: {ctx.channel.id}\n" \
                   f"\tChannel Name: {ctx.channel.name}\n" \
                   f"\tGuild ID: {ctx.guild.id}\n" \
                   f"\tGuild Name: {ctx.guild.name}\n" \
                   f"\tMember ID: {ctx.author.id}\n" \
                   f"\tMember Name: {ctx.author.name}\n" \
                   f"\tIs Owner: {is_owner}"
        self.log.info(response)
        await ctx.respond(response)

    @commands.guild_only()
    @is_in_channel(EVENT_BOT_CHANNEL_ID)
    @manager_group.command(name='unload_cog')
    async def _unload_cog(self, ctx, *, cog: Option(str, "What cog do you want to unload?")):
        self.log.info(f"unload_cog [cogs.{cog}] of {len(self.bot.extensions)}: {ctx.author.name}")

        if cog != "manager":
            try:
                self.bot.unload_extension(f"cogs.{cog}")
            except Exception as e:
                self.log.info(f"ERROR: unload_cog [cogs.{cog}]:{type(e).__name__}")
                await ctx.respond(f"**`ERROR:`** {type(e).__name__} - {e}")
            else:
                self.log.info(f"unload_cog [cogs.{cog}] of {len(self.bot.extensions)}: SUCCESS")
                await ctx.respond(f"**`SUCCESS`** {cog} Unloaded")
        else:
            await ctx.respond(f"**`ERROR:`** Cannot Unload Manager Cog")

    @commands.guild_only()
    @is_in_channel(EVENT_BOT_CHANNEL_ID)
    @manager_group.command(name='load_cog')
    async def _load_cog(self, ctx, *, cog: Option(str, "What cog do you want to load?")):
        self.log.info(f"load_cog [cogs.{cog}] of {len(self.bot.extensions)}: {ctx.author.name}")
        try:
            self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            self.log.info(f"ERROR: load_cog [cogs.{cog}]:{type(e).__name__}")
            await ctx.respond(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            self.log.info(f"load_cog [cogs.{cog}] of {len(self.bot.extensions)}: SUCCESS")
            await ctx.respond(f"**`SUCCESS`** {cog} Loaded")


def setup(bot):
    bot.add_cog(Manager(bot))
