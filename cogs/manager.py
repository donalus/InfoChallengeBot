import logging
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

LOGGING_STR = os.getenv('logging_str')
EVENT_GUILD_ID = int(os.getenv('event_guild_id'))
EVENT_BOT_CHANNEL_ID = int(os.getenv('event_bot_channel_id'))


def is_in_guild(guild_id):
    async def predicate(ctx):
        return ctx.guild and ctx.guild.id == guild_id

    return commands.check(predicate)


def is_in_channel(channel_id):
    async def predicate(ctx):
        return ctx.channel and ctx.channel.id == channel_id

    return commands.check(predicate)


class Manager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(LOGGING_STR)
        self.log.info(f"Booting up Cog: Registrations")

    @commands.command(name='test', hidden=True)
    @commands.guild_only()
    @is_in_guild(EVENT_GUILD_ID)
    @commands.is_owner()
    async def _test(self, ctx):
        self.log.info(f"test:\n"
                      f"Channel ID: {ctx.channel.id}\n"
                      f"Channel Name: {ctx.channel.name}\n"
                      f"Guild ID: {ctx.guild.id}\n"
                      f"Guild Name: {ctx.guild.name}\n"
                      f"Member ID: {ctx.author.id}\n"
                      f"Member Name: {ctx.author.name}")

    @_test.error
    async def _test_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"Error _test_error: {error}")

    @commands.command(name='unload_cog', hidden=True)
    @commands.guild_only()
    @is_in_guild(EVENT_GUILD_ID)
    @commands.is_owner()
    async def _unload_cog(self, ctx, *, cog: str):
        self.log.info(f"unload_cog [cogs.{cog}] of {len(self.bot.extensions)}: {ctx.author.name}")

        if cog != "manager":
            try:
                self.bot.unload_extension(f"cogs.{cog}")
            except Exception as e:
                self.log.info(f"ERROR: unload_cog [cogs.{cog}]:{type(e).__name__}")
                await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
            else:
                self.log.info(f"unload_cog [cogs.{cog}] of {len(self.bot.extensions)}: SUCCESS")
                await ctx.send(f"**`SUCCESS`** {cog} Unloaded")
        else:
            await ctx.send(f"**`ERROR:`** Cannot Unload Manager Cog")

    @_unload_cog.error
    async def _unload_cog_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"Error _unload_cog: {error}")

    @commands.command(name='load_cog', hidden=True)
    @commands.guild_only()
    @is_in_guild(EVENT_GUILD_ID)
    @commands.is_owner()
    async def _load_cog(self, ctx, *, cog: str):
        self.log.info(f"load_cog [cogs.{cog}] of {len(self.bot.extensions)}: {ctx.author.name}")
        try:
            self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            self.log.info(f"ERROR: load_cog [cogs.{cog}]:{type(e).__name__}")
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            self.log.info(f"load_cog [cogs.{cog}] of {len(self.bot.extensions)}: SUCCESS")
            await ctx.send(f"**`SUCCESS`** {cog} Loaded")

    @_load_cog.error
    async def _load_cog_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            self.log.info(f"Error _load_cog: {error}")


def setup(bot):
    bot.add_cog(Manager(bot))
