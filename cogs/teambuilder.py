from pathlib import Path
import os
import ssl

import discord
from discord.ext import commands
import logging



class TeamBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(LOGGING_STR)
        self.log.info(f"Booting up Cog: Registrations")
