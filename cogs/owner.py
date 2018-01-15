import discord
from discord.ext import commands
import sys
import traceback
import json
import copy

import config
import cogs.utils as utils

def setup(bot):
    bot.add_cog(Owner(bot))

class Owner:
    """Commands only for the bot owner"""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def load(self, ctx, *, extension: str=None):
        """
        Loads an extension/cog
        """

        if not extension:
            await ctx.send(f"{ctx.author} | You must specify an extension to load.")
            return
        try:
            self.bot.load_extension(extension)
        except Exception as e:
            await ctx.author.send(f"```py\n{traceback.format_exc()}\n```")
            await ctx.send(f"{ctx.author} | Failed to load extension: {extension}. Check your DMs for more details.")
            print(f"Failed to load extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{ctx.author} | {extension} loaded.")

    @commands.command()
    async def unload(self, ctx, *, extension: str=None):
        """
        Unloads an extension/cog
        """

        if not extension:
            await ctx.send(f"{ctx.author} | You must specify an extension to unload.")
            return
        try:
            self.bot.unload_extension(extension)
        except Exception as e:
            await ctx.author.send(f"```py\n{traceback.format_exc()}\n```")
            await ctx.send(f"{ctx.author} | Failed to unload extension: {extension}. Check your DMs for more details.")
            print(f"Failed to unload extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{ctx.author} | {extension} unloaded.")

    @commands.command(name="reload")
    async def reload_(self, ctx, *, extension: str=None):
        """
        Reloads an extension/cog
        """

        if not extension:
            await ctx.send(f"{ctx.author} | You must specify an extension to reload.")
            return
        try:
            self.bot.unload_extension(extension)
            self.bot.load_extension(extension)
        except Exception as e:
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            print(f"Failed to reload extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{ctx.author} | {extension} reloaded.")

    @commands.command()
    async def die(self, ctx):
        """
        Causes the bot to logout
        """

        await self.bot.db.close()
        await ctx.send(f"{ctx.author} | Database connection closed, logging out now.")
        await self.bot.logout()

    @commands.command()
    async def block(self, ctx, user: discord.User):
        """
        Prevents a user from using the bot
        """

        if user.id in self.bot.blocked:
            await ctx.send(f"{ctx.author} | {user} is already blocked, use {config.prefix}unblock <user> if you want to unblock them.")
            return

        self.bot.blocked.append(user.id)
        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """INSERT INTO blocked (id) VALUES ($1);"""
            await connection.execute(query, user.id)
        await self.bot.db.release(connection)

        await ctx.send(f"{ctx.author} | {user} was blocked.")

    @commands.command()
    async def unblock(self, ctx, user: discord.User):
        """
        Gives a user access to the bot again
        """

        if not user.id in self.bot.blocked:
            await ctx.send(f"{ctx.author} | {user} isn't blocked, user {config.prefix}block <user> if you want to block them.")
            return

        self.bot.blocked.remove(user.id)
        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """DELETE FROM blocked WHERE id = $1;"""
            await connection.execute(query, user.id)
        await self.bot.db.release(connection)

        await ctx.send(f"{ctx.author} | {user} was unblocked.")

    @commands.command()
    async def killpet(self, ctx, user: discord.User):
        """
        Kills a user's pet
        """

        profile = await utils.get_profile(self.bot, user.id)
        if not profile:
            await ctx.send(f"{ctx.author} | That user doesn't have a profile.")
            return

        pet = json.loads(profile["pet"])
        dead_pet = copy.copy(pet)
        dead_pet["health"] = 0

        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """UPDATE users SET pet = $1 WHERE id = $2;"""
            await connection.execute(query, json.dumps(dead_pet), user.id)
        await self.bot.db.release(connection)

        await ctx.send(f"{ctx.author} | {user}'s pet is now dead.")

    @commands.command()
    async def createpet(self, ctx, name: str, expansion: str, image: str):
        pet = {
            name: {
                "image": image,
                "nickname": name,
                "name": name,
                "age": 0,
                "expansion": expansion,
                "saturation": 40,
                "cleanliness": 40,
                "health": 40
            }
        }

        await ctx.send(f"```json\n{json.dumps(pet, indent=4)}```")