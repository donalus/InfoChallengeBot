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

## Quick Start 
To quickly get running 
1. Clone repository
2. cd into directory
3. Run `poetry install`
4. Edit the values in the dotenv file and rename to `.env`
5. Run `poetry run python src/bot.py`

## To Access Documentation
Documentation is provided through mkdocs. You can start up a mkdocs server with the command `poetry run mkdocs serve` 
after completing the installation instructions.
