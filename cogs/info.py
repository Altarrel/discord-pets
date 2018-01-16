from discord.ext import commands
import discord


class InfoCommands:
    """
    Info about the bot
    """

    def __init__(self, bot):
        bot.remove_command("help")
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def help(self, ctx):
        """
        Lists commands
        """
        help_msg = "```md\n"

        if self.bot.is_owner(ctx.author):
            help_msg += "# Owner\n" \
                "- load [ext] -> Loads an extension.\n" \
                "- unload [ext] -> Unloads an extension.\n" \
                "- reload [ext] -> Reloads an extension.\n" \
                "- block [user] -> Blocks a user from using the bot.\n" \
                "- unblock [user] -> Unblocks a user.\n" \
                "- die -> Kills the script, it will usually be revived by pm2.\n" \
                "- killpet [user] -> Kill a user's pet.\n"

        help_msg += "# Utility\n" \
            "- help -> Shows this message.\n" \
            "- invite -> Invite the bot to your server.\n" \
            "- info -> Gives some info about the bot.\n" \
            "# Items\n" \
            "- store -> List items in the store.\n" \
            "- inventory -> List items in your inventory.\n" \
            "- inv -> An alias for inventory.\n" \
            "- buy [item] -> Buy an item from the store.\n" \
            "# Pet\n" \
            "- start -> Get your first pet.\n" \
            "- hardreset -> Delete your profile.\n" \
            "- stats -> Check your stats.\n" \
            "- newpet -> Get a new pet if yours has passed away.\n" \
            "- play -> Play a minigame to earn coins.\n" \
            "- feed [item] -> Feed your pet a food item.\n" \
            "- clean [item] -> Clean your pet with a cleaning item.\n" \
            "```"

        await ctx.send(help_msg)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def info(self, ctx):
        """
        Gives some info about the bot
        """

        embed = discord.Embed(title="Info", description=f"{self.bot.user.mention} allows you to"
                                                        f" take care of a virtual pet in Discord.\nIt was made by "
                                                        f"Altarrel#1219 using the discord.py wrapper for the Discord"
                                                        f" API.\nIt is hosted on a Scaleway C1 VPS and utilizes PM2 to"
                                                        f" keep the bot online.\nDiscord Pets will continue to receive"
                                                        f" updates, adding new pets and features.\nIf you'd like to get"
                                                        f" in contact with Altarrel, or have any issues with or"
                                                        f" suggestions for the bot, you can [join the help server]"
                                                        f"(https://discord.gg/ke6bp6r).")

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invite(self, ctx):
        """
        Invite the bot to your server
        """

        await ctx.send(f"{ctx.author} | <https://discordapp.com/api/"
                       f"oauth2/authorize?client_id={self.bot.user.id}&permissions=0&scope=bot>")


def setup(bot):
    bot.add_cog(InfoCommands(bot))
