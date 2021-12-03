from pathlib import Path
import os
import ssl
import sqlite3
import discord
from discord.ext import commands
import logging
from validate_email_address import validate_email

current_dir = Path('.')
data_path = current_dir / "data"
db = sqlite3.connect("users.db")


class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger('--IC-BOT-DISCORD--')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot is True:
            return

        await member.send(
            f"Welcome,{member.name}, to the {self.bot.guilds[0].name} Discord!\n"
            f"You are new here. I need to know the email address "
            f"that you used to register for {self.bot.guilds[0].name}.\n"
            f"Please reply with just your email address."
        )
        db.execute('INSERT INTO  convo_step VALUES(?, ?)', (member.id, 0))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.command_prefix):
            return
        if not message.guild:
            count = db.execute('SELECT count(*) FROM reg_users WHERE userid=?', (message.author.id,)).fetchone()[0]
            self.log.info(f"User ID: {message.author.id} | {count}")
            if count > 0:
                await message.reply(
                    f"Silly, you are already registered."
                )
            else:
                step = db.execute('SELECT step FROM convo_step WHERE userid=?', (message.author.id,)).fetchone()
                if step is None:
                    await message.reply(
                        f"Hello {message.author.name}, it looks like you need to register "
                        f"for {self.bot.guilds[0].name}.\nPlease reply with just your email address."
                    )

                    db.execute('INSERT INTO  convo_step VALUES(?, ?)', (message.author.id, 0))
                else:
                    if validate_email(message.content):
                        await message.reply(
                            f"Hello {message.author.name}, that is a valid email address."
                        )
                    else:
                        await message.reply(
                            f"Hello {message.author.name}, that is not a valid email address.\n"
                            f"Please reply with only your email address."
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
    bot.add_cog(Registration(bot))
