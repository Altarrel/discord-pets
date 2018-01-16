import traceback
import asyncio
import sys

from discord.ext import commands
import aiohttp
import discord
import asyncpg

import config


async def run():
    description = "A bot written in Python by Altarrel"
    db = await asyncpg.create_pool(**config.POSTGRES_CREDENTIALS)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users(id bigint PRIMARY KEY, currency int, inventory text, pet text, graveyard text);
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS blocked(id bigint);
    """)

    blocked = await db.fetch("""SELECT * FROM blocked""")

    bot = DiscordPets(description=description, db=db, blocked=blocked)
    try:
        await bot.start(config.BOT_TOKEN)
    except KeyboardInterrupt:
        await db.close()
        await bot.logout()


class DiscordPets(commands.Bot):
    # I stole this from SourSpoon
    def __init__(self, **kwargs):
        super().__init__(
            description=kwargs.pop("description"),
            command_prefix=config.prefix,
            game=discord.Game(name=f"{config.prefix}help")
        )

        self.last_interactions = {}
        self.db = kwargs.pop("db")
        self.blocked = kwargs.pop("blocked")
        self.loop.create_task(self.load_all_extensions())

    async def on_message(self, message):
        # Stop certain users from using the bot
        if message.author.id in self.blocked:
            return
            
        await self.process_commands(message)

    # Post guild count to https://discordbots.org/

    async def on_ready(self):
        print(f"Username: {self.user.name}\n"
              f"ID: {self.user.id}\n")

        if self.user.id == 360498777468960769:
            return

        headers = {'Authorization': config.DBL_TOKEN}
        data = {'server_count': len(self.guilds)}
        api_url = 'https://discordbots.org/api/bots/' + str(self.user.id) + '/stats'
        async with aiohttp.ClientSession() as session:
            await session.post(api_url, data=data, headers=headers)
        print("Guild count posted to https://discordbots.org/")

    async def on_guild_join(self, guild):
        if self.user.id == 360498777468960769:
            return

        headers = {'Authorization': config.DBL_TOKEN}
        data = {'server_count': len(self.guilds)}
        api_url = 'https://discordbots.org/api/bots/' + str(self.user.id) + '/stats'
        async with aiohttp.ClientSession() as session:
            await session.post(api_url, data=data, headers=headers)

    async def on_guild_remove(self, guild):
        if self.user.id == 360498777468960769:
            return

        headers = {'Authorization': config.DBL_TOKEN}
        data = {'server_count': len(self.guilds)}
        api_url = 'https://discordbots.org/api/bots/' + str(self.user.id) + '/stats'
        async with aiohttp.ClientSession() as session:
            await session.post(api_url, data=data, headers=headers)

    async def load_all_extensions(self):
        await self.wait_until_ready()
        await asyncio.sleep(1)
        extensions = ("cogs.owner",
                      "cogs.pets",
                      "cogs.error_handler",
                      "cogs.info"
                      )
        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
