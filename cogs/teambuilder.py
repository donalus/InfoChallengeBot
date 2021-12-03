from pathlib import Path
import os
import ssl

import discord
from discord.ext import commands

class TeamBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot