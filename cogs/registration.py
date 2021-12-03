from pathlib import Path
import os
import ssl

import discord
from discord.ext import commands


class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot is True:
            return
        await member.send(
            f"Welcome to the InfoChallenge Discord server!"
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if not message.guild:
            await message.reply(
                f"I am replying to {message.author.name}"
            )

    @commands.command(name="help", aliases=["helpme", "help_me", "registration_help"])
    async def registration_help(self, ctx, *args):
        """
        Help on how to register
        :param ctx:
        :param args:
        :return:
        """
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
        await ctx.send(
            f"So you want to register?"
        )


def setup(bot):
    bot.add_cog(Registration(bot))
