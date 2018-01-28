from discord.ext import commands
import discord

from fuzzywuzzy import process as fuzz_process
import json

with open("./game_data/pets.json") as f:
    all_pets = json.load(f)

class InfoCommands:
    """
    Info about the bot
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def help(self, ctx):
        """
        Lists commands
        """
        help_msg = "```md\n"

        if await self.bot.is_owner(ctx.author):
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
            "- expansions -> Lists all expansions.\n" \
            "- pets [expansion] -> Lists all pets in specified expansion.\n" \
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

        embed = discord.Embed(title="Info")
        embed.add_field(name="Background", value=f"{self.bot.user.mention} allows you to"
                                                        f" take care of a virtual pet in Discord.\nIt was made by "
                                                        f"Altarrel#1219 using the discord.py wrapper for the Discord"
                                                        f" API.\nIt is hosted on a Scaleway C1 VPS and utilizes PM2 to"
                                                        f" keep the bot online.\nDiscord Pets will continue to receive"
                                                        f" updates, adding new pets and features.\nIf you'd like to get"
                                                        f" in contact with Altarrel, or have any issues with or"
                                                        f" suggestions for the bot, you can [join the help server]"
                                                        f"(https://discord.gg/ke6bp6r).")
        
        embed.add_field(name="Usage", value="All of the bot's commands have a 5 second cooldown to prevent spam.\n"
                                            "The bot will not notify you of this, your message will simply be ignored.\n"
                                            "For longer cooldowns, such as the 1 week on hardreset, the bot will notify you.")

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invite(self, ctx):
        """Invite the bot to your server
        """

        await ctx.send(f"{ctx.author} | <https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=19456&scope=bot>")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def expansions(self, ctx):
        """Lists all expansions
        """

        expansion_list = "```md\n"
        for expansion in all_pets.keys():
            expansion_list += f"- {expansion}\n"
        expansion_list += "```"
        await ctx.send(expansion_list)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pets(self, ctx, *, expansion: str):
        """Lists pets from an expansion
        """

        extract_expansion = fuzz_process.extractOne(expansion, all_pets.keys(), score_cutoff=70)
        try:
            fuzzy_expansion = extract_expansion[0]
        except TypeError:
            # In case it returns None and raises NoneType is not subscriptable
            fuzzy_expansion = None

        if fuzzy_expansion is None:
            await ctx.send(f"{ctx.author} | That expansion doesn't exist.")
            return
        pet_list = f"```md\n# Pets in {fuzzy_expansion}\n"
        for pet in all_pets[fuzzy_expansion].keys():
            pet_list += f"- {pet}\n"
        pet_list += "```"
        await ctx.send(pet_list)

    # @commands.command()
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # async def view(self, ctx, *, pet: str):
    #     """Shows you the picture of a pet
    #     """

    #     extract_pet = fuzz_process.extractOne(pet, all_pets.items(), score_cutoff=70)
    #     print(extract_pet)

def setup(bot):
    bot.add_cog(InfoCommands(bot))
