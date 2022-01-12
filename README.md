# InfoChallengeBot
Discord Registration Bot for the UMD Information Challenge

## What is the UMD Information Challenge?

The [UMD Information Challenge](https://infochallenge.ischool.umd.edu/) is a week-long event 
that gathers teams of students from across multiple academic institutions to work with 
partnering organizations to address real-world problems, provide valuable team-building 
experience, and network with industry professionals.

More information about the UMD Information Challenge can be found at its website at:
https://infochallenge.ischool.umd.edu/

## Features

The InfoChallengeBot currently provides:
- Registration support through a very basic chatbot
- Basic moderation support (message deletion)
- Team creation and deletion

## This is not a Product

This bot requires a significant amount of programming and technical know-how and is not currently 
intended as an off-the-shelf product. The authors and contributors to this project may respond to 
your questions, but use at your own risk.

## Installing


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

### Steps to install locally:

1. Clone repository && cd into directory
2. Run `poetry install`
3. Run `poetry run python src/bot.py`

### Steps to run in docker:

1. Clone repository && cd into directory
2. Run `docker build -f docker/Dockerfile -t infochallengebot . && docker run --name InfoChallengeBot infochallengebot `