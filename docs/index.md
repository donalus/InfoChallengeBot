# Welcome to InfoChallengeBot

InfoChallengeBot is a Discord bot that was build to help manage the UMD Information Challenge Discord server. 
It provides registration and moderation features. 

## Installing

This project is not a product. Use at your own risk.

### Requirements
- **Python 3.8 or greater is required.**
- [Poetry](https://github.com/python-poetry/poetry)
- [Docker](https://www.docker.com/)
- Platform-specific:
    - Windows: 
        - Microsoft C++ Build Tools
    - Linux:
        - Dev tools

### Configuration

This project uses a dotenv file to pass "secret" information to the application. The most important of which is 
the discord bot token. Information about getting a bot token can be found here: https://discord.com/developers/applications

This bot requires the following:

Scopes:
- bot
- application.commands
- 
Bot Permissions:
- Administrator

The bot also requires the following Privileged Gateway Intents:
- Presence Intent
- Server Members Intent
- Message Content Intent

In the future, it may be possible to reduce the number of permissions required for the bot to run.

### Steps to run locally:

1. Clone repository
2. cd into directory
3. Run `poetry install`
4. Edit the values in the dotenv file and rename to `.env`
5. Run `poetry run python src/bot.py`

### Steps to run in docker:

1. Clone repository
2. cd into directory
3. Edit the values in the dotenv file and rename to `.env`
4. Run `docker build -f docker/Dockerfile -t infochallengebot . && docker run --name InfoChallengeBot infochallengebot`

## Commands

Commands are provided through the various cogs that are loaded.

### Manager

This cog provides basic moderation functionality and commands to manage InfoChallengeBot.

`/manager debug` [Restricted to Guild Owner and Bot Manager Role] prints the following debug information

- Guild ID - The snowflake representing the guild ID
- Channel ID - The snowflake representing the channel ID
- Channel Name - The name of the current channel
- Member ID - The snowflake representing the current issuing the command
- Member Name - The name of the current issuing the command
- Is Owner - A boolean indicating whether the current user is the owner
- Team Role ID - The snowflake representing the role that is able to control InfoChallengeBot

`/manager load_cog` [Restricted to Guild Owner] loads a cog that provides additional functionality to the 
InfoChallengeBot

`/manager unload_cog` [Restricted to Guild Owner] unloads a cog and disables the functionality that it provides to 
the InfoChallengeBot

`/manager purge` [Restricted to Guild Owner and Bot Manager Role] deletes messages from the Discord server

The following options can be used to the purge command:

- channel: the name of the channel to delete messages from 
- user: the name of the author of the messages to delete 
- limit: the number of messages to be deleted


### Registrator 

The primary functionality of the registrator cog is the chatbot that guides the participant through registration. 

`/reg reset` [Restricted to Guild Owner and Bot Manager Role] resets a user's registration by deleting the 
corresponding entries in the database and removing roles.

### TeamBuilder 

The TeamBuilder cog provides commands to manage teams.

A team is made up of:

- A _category channel_ named after the team in the format `TEAM-{num}`
- A _text channel_ in the format `team-{num}-text`
- A _voice channel_ in the format `team-{num}-voice`

Permissions are set on the _category channel_ to restrict access to only the team members, their mentor, and 
event staff.

`/teams create` [Restricted to Guild Owner] creates a specific number of teams.

`/teams delete` [Restricted to Guild Owner] deletes a specific number of teams. 

