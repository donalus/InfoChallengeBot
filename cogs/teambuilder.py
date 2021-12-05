from pathlib import Path
import os
import ssl

import discord
from discord.ext import commands
import logging

from dotenv import load_dotenv
load_dotenv()

LOGGING_STR = os.getenv('logging_str')


class TeamBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(LOGGING_STR)
        self.log.info(f"Booting up Cog: TeamBuilder")


def setup(bot):
    bot.add_cog(TeamBuilder(bot))
