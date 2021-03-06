from discord.ext import commands

import config


class GuildLogs:
    """
    Guild join, remove, and count
    """

    def __init__(self, bot):
        self.bot = bot

    async def on_guild_join(self, guild):
        log_channel = self.bot.get_channel(config.log_channel_id)

        msg = f"__**Guild Join**__\n\n**Name:** {guild.name}\n**ID:** {guild.id}\n" \
              f"**Member Count:** {len(guild.members)}"
        await log_channel.send(msg)

    async def on_guild_join(self, guild):
        log_channel = self.bot.get_channel(config.log_channel_id)

        msg = f"__**Guild Remove**__\n\n**Name:** {guild.name}\n**ID:** {guild.id}\n" \
              f"**Member Count:** {len(guild.members)}"
        await log_channel.send(msg)

    @commands.command()
    async def guildcount(self, ctx):
        await ctx.send(len(self.bot.guilds))


def setup(bot):
    bot.add_cog(GuildLogs(bot))
