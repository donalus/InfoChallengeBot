import logging
from pathlib import Path
import discord
from discord.ext import commands
import os


# logging config
# logging.basicConfig(
#     filename="log/ic-bot.log",
#     format="%(asctime)s - %(message)s",
#     level=logging.INFO,
#     datefmt="%d-%b-%y %H:%M:%S",
# )


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


current_dir = Path('.')
data_path = current_dir / "data"

# Extensions (cogs) to load
extensions = ["registration"]

# Load configuration from environment
go_for_launch = True
try:
    logging.info("Loading config...")

    bot_token = os.environ["token"]
    bot_key = os.environ["key"]
except KeyError as e:
    logging.critical(f"Configuration error. \n\tKey Not Found: {e}")
    go_for_launch = False

# Configure intents
intents = discord.Intents.default()
intents.members = True

# Set up the bot
bot = commands.Bot(
    command_prefix=bot_key,
    description=f"Registration Bot for InfoChallenge",
    intents=intents)
bot.remove_command('help')


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching,
                                  name="registration")
    )
    logging.info("Bot is ready!")


if __name__ == '__main__':
    logging = get_module_logger(__name__)
    logging.info("hit main")

    cog_count = 0
    for extension in extensions:
        try:
            bot.load_extension(f"cogs.{extension}")
            logging.info(f"Loaded Cog: {extension}")
            cog_count += 1
        except Exception as error:
            logging.warning(f"Cog Error: {extension} could not be loaded.\nt[{error}]")

        logging.info(f"Loaded {cog_count}/{len(extensions)} cogs.")

    if go_for_launch:
        logging.info("Houston, we are go for launch!")
        bot.run(bot_token)
    else:
        logging.warning("Abort, abort, abort.")
