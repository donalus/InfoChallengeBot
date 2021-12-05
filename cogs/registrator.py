from pathlib import Path
import os
import ssl
import discord
from discord.ext import commands
import logging
from validate_email_address import validate_email
from models import Session, Registration, ConvoStep, Participant

from dotenv import load_dotenv


load_dotenv()

IS_PRODUCTION = os.getenv('is_production')
EVENT_NAME = os.getenv('event_name')
DATA_DIR = os.getenv('data_dir')
BOT_KEY = os.getenv('bot_prefix')
LOGGING_STR = os.getenv('logging_str')
current_dir = Path('.')
data_path = current_dir / DATA_DIR


class Registrator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(LOGGING_STR)
        self.log.info(f"Booting up Cog: Registrations")

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

        session = Session()
        session.add(ConvoStep(discord_id=member.id, step=0))
        session.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.command_prefix):
            return
        if not message.guild:
            session = Session()
            count = session.query(Participant).filter(Participant.discord_id == message.author.id).count()

            self.log.info(f"User ID: {message.author.id} | {count}")
            if count > 0:
                await message.reply(
                    f"Silly, you are already registered."
                )
            else:
                convo = session.query(ConvoStep).filter(ConvoStep.discord_id == message.author.id).one_or_none()

                if convo is None:
                    await message.reply(
                        f"Hello {message.author.name}, it looks like you need to register "
                        f"for {self.bot.guilds[0].name}.\nPlease reply with just your email address."
                    )

                    session.add(ConvoStep(discord_id=message.author.id, step=0))
                    session.commit()
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
    bot.add_cog(Registrator(bot))
