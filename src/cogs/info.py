import discord
from discord.ext import commands

def setup(bot):
    bot.add_cog(Info(bot))

class Info:
    """Commands that return info about the bot
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def invite(self, ctx):
        permissions = discord.Permissions()
        permissions.update(send_messages=True, read_messages=True, embed_links=True)
        url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        await ctx.send(url)
