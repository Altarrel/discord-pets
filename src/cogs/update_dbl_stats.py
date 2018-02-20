import discord
from discord.ext import commands

import config

def setup(bot):
    bot.add_cog(DBL(bot))

class DBL:
    """Update stats on https://discordbots.org/
    """

    def __init__(self, bot):
        self.bot = bot
        self.token = config.token

    async def update_stats(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            
