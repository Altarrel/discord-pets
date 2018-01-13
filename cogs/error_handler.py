import discord
from discord.ext import commands
import sys
import traceback

import cogs.utils as utils

def setup(bot):
    bot.add_cog(ErrorHandler(bot))

class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ctx.author}, you must provide {utils.a_or_an(error.param.name)} {error.param.name}.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"{ctx.author}, you can use that command again in {error.retry_after:.2f} seconds.")
        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)