from discord.ext import commands

# This is a mixin to make sure that these commands only work in the channel specified.
def is_in_channel(channel_id):
    async def channel_predicate(ctx):
        return ctx.channel and ctx.channel.id == channel_id

    return commands.check(channel_predicate)
