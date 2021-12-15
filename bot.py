import logging
from pathlib import Path
import discord
from discord.ext import commands
from discord.commands import Option
import os
from dotenv import load_dotenv
from models import init_db

load_dotenv()

IS_PROD = os.environ['is_production'] == 'True'
DB_CONN = os.getenv('db_conn_uri')
EVENT_NAME = os.getenv('event_name')
EVENT_GUILD_ID = int(os.getenv('event_guild_id'))
DATA_DIR = os.getenv('data_dir')
LOGGING_STR = os.getenv('logging_str')
BOT_KEY = os.getenv('bot_prefix')
BOT_TOKEN = os.getenv('bot_token')

EVENT_BOT_ROLES = ['Planning Team']
current_dir = Path('.')
data_path = current_dir / DATA_DIR


def get_module_logger(mod_name):
    """
    To use this, do logger = get_module_logger(__name__)
    """
    logger = logging.getLogger(mod_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


# Extensions (cogs) to load
extensions = ["manager", "registrator", "teambuilder"]

# Configure intents
intents = discord.Intents.default()
intents.members = True
intents.typing = False

# Set up the bot
bot = commands.Bot(
    command_prefix=BOT_KEY,
    description=f"Registration Bot for {EVENT_NAME}",
    intents=intents)
bot.remove_command('help')


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching,
                                  name=EVENT_NAME)
    )
    log.info(f"Bot is ready for {EVENT_NAME}!")
    for guild in bot.guilds:
        log.info(f"Bot is connected to {guild.id}")


if __name__ == '__main__':
    log = get_module_logger('IC-BOT-DISCORD')
    log.info(f"Start automatic ground launch sequencer.")

    init_db()

    cog_count = 0
    for extension in extensions:
        try:
            bot.load_extension(f"cogs.{extension}")
            log.info(f"Loaded Cog: {extension}")
            cog_count += 1
        except Exception as error:
            log.warning(f"Cog Error: {extension} could not be loaded.\n\t[{error}]")

        log.info(f"Loaded {cog_count}/{len(extensions)} cogs.")

    log.info(f"Main engine start. Go for launch!")
    bot.run(BOT_TOKEN)
