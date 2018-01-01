import discord
from discord.ext import commands
import json
import time
import math
import asyncio
import random

import cogs.utils as utils
from game_data.minigames import all_minigames

def setup(bot):
    bot.add_cog(Pets(bot))

class Pets:
    """Pet related commands"""

    def __init__(self, bot):
        self.bot = bot

    async def get_profile(self, user_id):
        profile = await self.bot.db.fetchrow("SELECT * FROM users WHERE id = $1;", user_id)
        return profile

    @commands.command()
    async def start(self, ctx):
        """Get your first pet"""

        profile = await self.get_profile(ctx.author.id)
        if profile:
            await ctx.send(f"You already have a profile, use {ctx.prefix}hardreset "\
                "if you want to delete it.")
            return

        pet_expansion, new_pet = utils.pick_new_pet()

        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """INSERT INTO users (id, currency, inventory, pet, graveyard)
                VALUES ($1, $2, $3, $4, $5);"""
            await connection.execute(query, ctx.author.id, 0, "{}", json.dumps(new_pet), "{}")
        await self.bot.db.release(connection)

        profile = {"pet": json.dumps(new_pet), "currency": 0, "graveyard": "[]"}
        stats_embed = utils.create_stats_embed(ctx.author.name, profile)

        current_time = math.floor(time.time() / 60)
        self.bot.last_interactions[ctx.author.id] = {
            "fed": current_time,
            "cleaned": current_time,
            "play": current_time
        }

        await ctx.send(f"Your first pet is **{new_pet['name']}** from the **{pet_expansion}** expansion.", embed=stats_embed)

    @commands.command()
    async def hardreset(self, ctx):
        """Delete your profile"""

        profile = await self.get_profile(ctx.author.id)
        if not profile:
            await ctx.send(f"You don't have a profile, use {ctx.prefix}start to get one.")
            return

        await ctx.send(f"This will delete your profile. You will lose your pet, currency, and inventory. "\
            f"You will be able to use the bot again with {ctx.prefix}start, but you will be starting over. Say CONFIRM to confirm the deletion of your profile.")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.message.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond, reset canceled.")
            return

        if msg.content == "CONFIRM":
            connection = await self.bot.db.acquire()
            async with connection.transaction():
                query = """DELETE FROM users WHERE id = $1"""
                await connection.execute(query, ctx.author.id)
            await self.bot.db.release(connection)
            await ctx.send("Your profile was deleted.")
        else:
            await ctx.send("Invalid response, reset canceled.")

    @commands.command()
    async def stats(self, ctx):
        """Check your stats"""

        profile = await self.get_profile(ctx.author.id)
        if not profile:
            await ctx.send(f"You don't have a profile, use {ctx.prefix}start to get one.")
            return

        pet = json.loads(profile["pet"])
        graveyard = json.loads(profile["graveyard"])
        current_time = math.floor(time.time() / 60)
        try:
            last_interactions = self.bot.last_interactions[ctx.author.id]
            decayed_stats = utils.decay_stats(pet, current_time, last_interactions)
        except KeyError:
            decayed_stats = pet
            self.bot.last_interactions[ctx.author.id] = {
                "fed": current_time,
                "cleaned": current_time,
                "play": current_time
            }

        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """UPDATE users SET pet = $1 WHERE id = $2;"""
            await connection.execute(query, json.dumps(decayed_stats), ctx.author.id)
        await self.bot.db.release(connection)

        profile = await self.get_profile(ctx.author.id)
        stats_embed = utils.create_stats_embed(ctx.author.name, profile)
        await ctx.send(embed=stats_embed)

    @commands.command(aliases=["inv"])
    async def inventory(self, ctx):
        """Check your inventory"""

        profile = await self.get_profile(ctx.author.id)
        if not profile:
            await ctx.send(f"You don't have a profile, use {ctx.prefix}start to get one.")
            return

        inventory = json.loads(profile["inventory"])
        msg = f"```\nInventory of {ctx.author}\n\n"
        if not a:
            for item in inventory:
                msg += f"-{item}: {inventory[item]}\n"
        else:
            msg += "Empty inventory"
        msg += "```"
        await ctx.send(msg)

    @commands.command()
    async def play(self, ctx):
        """
        Play a game to win pet coins
        """

        profile = await self.get_profile(ctx.author.id)
        if not profile:
            await ctx.send(f"You don't have a profile, use {ctx.prefix}start to get one.")
            return

        minigame = random.choice(all_minigames)
        await minigame(self.bot, ctx)