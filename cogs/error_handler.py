import traceback
import sys

from discord.ext import commands

import cogs.utils as utils


class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ctx.author}, you must provide {utils.a_or_an(error.param.name)} {error.param.name}.")
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.command.name != "hardreset":
                return
            await ctx.send(f"{ctx.author}, you can use that command again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, commands.NotOwner):
            await ctx.send(f"{ctx.author} | You don't have permission to use that command.")
        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
