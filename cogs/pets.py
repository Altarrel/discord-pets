import asyncio
import random
import json
import time
import copy

from fuzzywuzzy import process as fuzz_process
from discord.ext import commands
import discord

import cogs.utils as utils
from game_data.minigames import all_minigames


with open("./game_data/store.json", "r") as f:
    store = json.load(f)


class Pets:
    """
    Pet related commands
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def start(self, ctx):
        """
        Get your first pet
        """

        profile = await utils.get_profile(self.bot, ctx.author.id)
        if profile:
            await ctx.send(f"{ctx.author} | You already have a profile, use {ctx.prefix}hardreset "
                           f"if you want to delete it.")
            return

        pet_expansion, new_pet = utils.pick_new_pet(None)
        new_pet["birth_time"] = int(time.time() / 60)

        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """INSERT INTO users (id, currency, inventory, pet, graveyard)
                VALUES ($1, $2, $3, $4, $5);"""
            await connection.execute(query, ctx.author.id, 0, "{}", json.dumps(new_pet), "{}")
        await self.bot.db.release(connection)

        profile = {"pet": json.dumps(new_pet), "currency": 0, "graveyard": "[]"}
        stats_embed = utils.create_stats_embed(ctx.author.name, profile)

        current_time = int(time.time() / 60)
        self.bot.last_interactions[ctx.author.id] = {
            "fed": current_time,
            "cleaned": current_time
        }

        await ctx.send(f"{ctx.author} | Your first pet is **{new_pet['name']}** from the **{pet_expansion}**"
                       f" expansion.", embed=stats_embed)

    @commands.command()
    @commands.cooldown(1, 604800, commands.BucketType.user)
    async def hardreset(self, ctx):
        """
        Delete your profile
        """

        profile = await utils.get_profile(self.bot, ctx.author.id)
        if not profile:
            await ctx.send(f"{ctx.author} | you don't have a profile, use {ctx.prefix}start to get one.")
            return

        await ctx.send(f"{ctx.author} | This will delete your profile. You will lose your pet, currency, and inventory."
                       f" You will be able to use the bot again with {ctx.prefix}start, but you will be starting over."
                       f" Say CONFIRM to confirm the deletion of your profile.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author} | You took too long to respond, reset canceled.")
            return

        if msg.content == "CONFIRM":
            connection = await self.bot.db.acquire()
            async with connection.transaction():
                query = """DELETE FROM users WHERE id = $1"""
                await connection.execute(query, ctx.author.id)
            await self.bot.db.release(connection)
            await ctx.send(f"{ctx.author} | Your profile was deleted.")
        else:
            await ctx.send(f"{ctx.author} | Invalid response, reset canceled.")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stats(self, ctx):
        """
        Check your stats
        """

        profile = await utils.get_profile(self.bot, ctx.author.id)
        if not profile:
            await ctx.send(f"{ctx.author} | You don't have a profile, use {ctx.prefix}start to get one.")
            return

        pet = json.loads(profile["pet"])
        current_time = int(time.time() / 60)
        try:
            last_interactions = self.bot.last_interactions[ctx.author.id]
            decayed_stats = utils.decay_stats(pet, current_time, last_interactions)
        except KeyError:
            decayed_stats = pet
            self.bot.last_interactions[ctx.author.id] = {
                "saturation": current_time,
                "cleanliness": current_time
            }

        new_profile = dict(profile)
        new_profile["pet"] = json.dumps(decayed_stats)
        stats_embed = utils.create_stats_embed(ctx.author.name, new_profile)
        await ctx.send(embed=stats_embed)

    @commands.command(aliases=["inv"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def inventory(self, ctx):
        """
        Check your inventory
        """

        profile = await utils.get_profile(self.bot, ctx.author.id)
        if not profile:
            await ctx.send(f"{ctx.author} | You don't have a profile, use {ctx.prefix}start to get one.")
            return

        inventory = json.loads(profile["inventory"])
        msg = f"```\nInventory of {ctx.author}\n\n"
        original_msg = copy.copy(msg)
        for item in inventory:
            if inventory[item]["amount"] > 0:
                msg += f"-{item}: {inventory[item]['amount']}\n"
        if msg == original_msg:
            await ctx.send(f"{ctx.author} | Your inventory is empty.")
            return
        msg += "```"
        await ctx.send(msg)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def play(self, ctx):
        """
        Play a game to win pet coins
        """

        profile = await utils.get_profile(self.bot, ctx.author.id)
        if not profile:
            await ctx.send(f"{ctx.author} | You don't have a profile, use {ctx.prefix}start to get one.")
            return

        # Death check
        pet = json.loads(profile["pet"])
        if pet["health"] <= 0 or pet["age"] >= 14:
            await ctx.send(f"{ctx.author} | {pet['nickname']} is no longer with us.")
            return

        minigame = random.choice(all_minigames)
        await minigame(self.bot, ctx)

    @commands.group()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def store(self, ctx):
        """
        Items for your pet
        """

        embed = discord.Embed(title=f"{ctx.author} | Store")
        for item in store:
            if store[item]["amount"] > 0:
                embed.add_field(name=item, value=f"Price: {store[item]['price']}\nStat Restore Type:"
                                                 f" {store[item]['restore_type'].title()}\nStat Restore Amount:"
                                                 f" {store[item]['restore_amount']}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def buy(self, ctx, *, item: str):
        """
        Buy items for your pet
        """

        profile = await utils.get_profile(self.bot, ctx.author.id)
        if not profile:
            await ctx.send(f"{ctx.author} | You don't have a profile, use {ctx.prefix}start to get one.")
            return

        extract_item = fuzz_process.extractOne(item, store.keys(), score_cutoff=70)
        try:
            store_item = extract_item[0]
        except TypeError:
            store_item = None

        if not store_item:
            await ctx.send(f"{ctx.author} | That item isn't in the store.")
            return

        balance = profile["currency"]
        price = store[store_item]["price"]

        if price > balance:
            await ctx.send(f"{ctx.author} | You don't have enough coins to buy {store_item}.")
            return
        else:
            balance -= price
            inventory = json.loads(profile["inventory"])
            if store_item in inventory:
                inventory[store_item]["amount"] += store[store_item]["amount"]
            else:
                inventory[store_item] = store[store_item]
            connection = await self.bot.db.acquire()
            async with connection.transaction():
                query = """UPDATE users SET currency = $1, inventory = $2 WHERE id = $3"""
                await connection.execute(query, balance, json.dumps(inventory), ctx.author.id)
            await self.bot.db.release(connection)

            await ctx.send(f"{ctx.author} | You bought {store[store_item]['amount']} {store_item} for {price} coins.")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def feed(self, ctx, item: str):
        """
        Feed your pet
        """
        profile = await utils.get_profile(self.bot, ctx.author.id)
        if not profile:
            await ctx.send(f"{ctx.author} | You don't have a profile, use {ctx.prefix}start to get one.")
            return

        pet = json.loads(profile["pet"])
        # Early pet death checking
        if pet["health"] <= 0 or pet["age"] >= 14:
            await ctx.send(f"{ctx.author} | {pet['nickname']} is no longer with us.")
            return

        inventory = json.loads(profile["inventory"])
        extract_item = fuzz_process.extractOne(item, inventory.keys(), score_cutoff=70)
        try:
            fuzzy_item_name = extract_item[0]
            fuzzy_item = inventory[fuzzy_item_name]
        except TypeError:
            fuzzy_item_name = None
            fuzzy_item = None
        current_time = int(time.time() / 60)

        try:
            last_interactions = self.bot.last_interactions[ctx.author.id]
            # Only decay one stat so that stats aren't decreased an extra time
            decayed_stats = utils.decay_stat(pet, "saturation", current_time, last_interactions)
        except KeyError:
            decayed_stats = pet
            self.bot.last_interactions[ctx.author.id] = {
                "saturation": current_time,
                "cleanliness": current_time
            }
        else:
            self.bot.last_interactions[ctx.author.id]["saturation"] = current_time

        # Check to make sure their pet didn't die
        # If it did, update the graveyard and stop them from being able to use commands properly
        # until they get a new one
        if decayed_stats["health"] <= 0 or decayed_stats["age"] >= 14:
            graveyard = json.loads(profile["graveyard"])
            graveyard.append(pet)

            connection = await self.bot.db.acquire()
            async with connection.transaction():
                query = """UPDATE users SET pet = $1, graveyard = $2 WHERE id = $3;"""
                await self.bot.db.execute(query, json.dumps(pet), json.dumps(graveyard), ctx.author.id)
            await self.bot.db.release(connection)
            await ctx.send(f"{ctx.author} | {pet['nickname']} has passed away.")
            return

        # These come after death check because death message should override
        if not fuzzy_item or fuzzy_item["amount"] <= 0:
            await ctx.send(f"{ctx.author} | You don't have that item in your inventory.")
            return

        if fuzzy_item["restore_type"] != "saturation":
            await ctx.send(f"{ctx.author} | {fuzzy_item_name} isn't a food item.")
            return

        if decayed_stats["saturation"] == 40:
            await ctx.send(f"{ctx.author} | {pet['nickname']} is full.")
            return

        decayed_stats["saturation"] += fuzzy_item["restore_amount"]

        if decayed_stats["saturation"] > 40:
            decayed_stats["saturation"] = 40

        inventory[fuzzy_item_name]["amount"] -= 1

        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """UPDATE users SET inventory = $1, pet = $2 WHERE id = $3"""
            await connection.execute(query, json.dumps(inventory), json.dumps(decayed_stats), ctx.author.id)
        await self.bot.db.release(connection)

        await ctx.send(f"{ctx.author} | {utils.possessive(pet['nickname'])} saturation was increased by "
                       f"{fuzzy_item['restore_amount']}.")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clean(self, ctx, item: str):
        """
        Clean your pet
        """
        profile = await utils.get_profile(self.bot, ctx.author.id)
        if not profile:
            await ctx.send(f"{ctx.author} | You don't have a profile, use {ctx.prefix}start to get one.")
            return

        pet = json.loads(profile["pet"])
        # Early pet death checking
        if pet["health"] <= 0 or pet["age"] >= 14:
            await ctx.send(f"{ctx.author} | {pet['nickname']} is no longer with us.")
            return

        inventory = json.loads(profile["inventory"])
        # Get the item from inventory using fuzzy string matching
        extract_item = fuzz_process.extractOne(item, inventory.keys(), score_cutoff=70)
        try:
            fuzzy_item_name = extract_item[0]
            fuzzy_item = inventory[fuzzy_item_name]
        except TypeError:
            fuzzy_item_name = None
            fuzzy_item = None
        current_time = int(time.time() / 60)

        try:
            last_interactions = self.bot.last_interactions[ctx.author.id]
            # Only decay one stat so that saturation isn't decreased an extra time
            decayed_stats = utils.decay_stat(pet, "cleanliness", current_time, last_interactions)
        except KeyError:
            decayed_stats = pet
            self.bot.last_interactions[ctx.author.id] = {
                "saturation": current_time,
                "cleanliness": current_time,
            }
        else:
            self.bot.last_interactions[ctx.author.id]["cleanliness"] = current_time

        # Check to make sure their pet didn't die
        # If it did, update the graveyard and stop them from being able to use commands properly
        # until they get a new one
        if decayed_stats["health"] <= 0 or decayed_stats["age"] >= 14:
            graveyard = json.loads(profile["graveyard"])
            graveyard.append(pet)

            connection = await self.bot.db.acquire()
            async with connection.transaction():
                query = """UPDATE users SET pet = $1, graveyard = $2 WHERE id = $3;"""
                await self.bot.db.execute(query, json.dumps(pet), json.dumps(graveyard), ctx.author.id)
            await self.bot.db.release(connection)
            await ctx.send(f"{ctx.author} | {pet['nickname']} has passed away.")
            return

        if not fuzzy_item or fuzzy_item["amount"] <= 0:
            await ctx.send(f"{ctx.author} | You don't have that item in your inventory.")
            return

        if fuzzy_item["restore_type"] != "cleanliness":
            await ctx.send(f"{ctx.author} | {fuzzy_item_name} isn't a cleaning item.")
            return

        if decayed_stats["cleanliness"] == 40:
            await ctx.send(f"{ctx.author} | {pet['nickname']} is already spotless.")
            return

        decayed_stats["cleanliness"] += fuzzy_item["restore_amount"]

        if decayed_stats["cleanliness"] > 40:
            decayed_stats["cleanliness"] = 40

        inventory[fuzzy_item_name]["amount"] -= 1

        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """UPDATE users SET inventory = $1, pet = $2 WHERE id = $3"""
            await connection.execute(query, json.dumps(inventory), json.dumps(decayed_stats), ctx.author.id)
        await self.bot.db.release(connection)

        await ctx.send(f"{ctx.author} | {utils.possessive(pet['nickname'])} cleanliness was increased by "
                       f"{fuzzy_item['restore_amount']}.")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def newpet(self, ctx):
        """
        Get a new pet
        """

        profile = await utils.get_profile(self.bot, ctx.author.id)
        if not profile:
            await ctx.send(f"{ctx.author} | You don't have a profile, use {ctx.prefix}start to get one.")
            return

        pet = json.loads(profile["pet"])
        current_time = int(time.time() / 60)
        try:
            last_interactions = self.bot.last_interactions[ctx.author.id]
            decayed_stats = utils.decay_stats(pet, current_time, last_interactions)
        except KeyError:
            decayed_stats = pet
            self.bot.last_interactions[ctx.author.id] = {
                "saturation": current_time,
                "cleanliness": current_time,
            }

        # Alive check so you can only get a new pet if your current one is dead
        if decayed_stats["health"] > 0 and decayed_stats["age"] < 14:
            await ctx.send(f"{ctx.author} | You can't get a new pet right now.")
            return

        pet_expansion, new_pet = utils.pick_new_pet(pet)
        new_pet["birth_time"] = int(time.time() / 60)

        graveyard = json.loads(profile["graveyard"])
        graveyard.append(decayed_stats)
        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """UPDATE users SET pet = $1, graveyard = $2 WHERE id = $3"""
            await connection.execute(query, json.dumps(new_pet), json.dumps(graveyard), ctx.author.id)
        await self.bot.db.release(connection)

        profile = {"pet": json.dumps(new_pet), "currency": 0, "graveyard": json.dumps(graveyard)}
        stats_embed = utils.create_stats_embed(ctx.author.name, profile)

        current_time = int(time.time() / 60)
        self.bot.last_interactions[ctx.author.id] = {
            "saturation": current_time,
            "cleanliness": current_time
        }

        await ctx.send(f"{ctx.author} | Your new pet is **{new_pet['name']}** from the **{pet_expansion}** expansion.",
                       embed=stats_embed)


def setup(bot):
    bot.add_cog(Pets(bot))
