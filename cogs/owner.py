import discord
from discord.ext import commands
import sys
import traceback

def setup(bot):
    bot.add_cog(Owner(bot))

class Owner:
    """Commands only for the bot owner"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, *, extension: str=None):
        """Loads an extension/cog"""

        if not extension:
            await ctx.send("You must specify an extension to load.")
            return
        try:
            self.bot.load_extension(extension)
        except Exception as e:
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            print(f"Failed to load extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{extension} loaded.")

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, *, extension: str=None):
        """Unloads an extension/cog"""

        if not extension:
            await ctx.send("You must specify an extension to unload.")
            return
        try:
            self.bot.unload_extension(extension)
        except Exception as e:
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            print(f"Failed to load extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{extension} unloaded.")

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_(self, ctx, *, extension: str=None):
        """Reloads an extension/cog"""

        if not extension:
            await ctx.send("You must specify an extension to reload.")
            return
        try:
            self.bot.unload_extension(extension)
            self.bot.load_extension(extension)
        except Exception as e:
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            print(f"Failed to reload extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{extension} reloaded.")

    @commands.command()
    @commands.is_owner()
    async def exit(self, ctx):
        """Causes the bot to logout"""

        await self.bot.db.close()
        await ctx.send("Database connection closed, logging out now.")
        await self.bot.logout()