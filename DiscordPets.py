import discord
from discord.ext import commands
import asyncio
import asyncpg
import sys
import traceback

import config

async def run():
    description = "A bot written in Python by Altarrel"
    pg = {"user": "postgres", "password": "discord-pets", "database": "postgres", "host": "127.0.0.1"}
    db = await asyncpg.create_pool(**pg)
    await db.execute("CREATE TABLE IF NOT EXISTS users(id bigint PRIMARY KEY, currency int, inventory text, pet text, graveyard text);")

    bot = DiscordPets(description=description, db=db)
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        await db.close()
        await bot.logout()

class DiscordPets(commands.Bot):
    # I stole this from SourSpoon
    def __init__(self, **kwargs):
        super().__init__(
            description=kwargs.pop("description"),
            command_prefix="dp!"
        )

        self.last_interactions = {}
        self.db = kwargs.pop("db")
        self.loop.create_task(self.load_all_extensions())

    async def load_all_extensions(self):
        await self.wait_until_ready()
        await asyncio.sleep(1)
        extensions = ("cogs.owner",
                      "cogs.pets")
        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):
        print(f"Username: {self.user.name}\n"
              f"ID: {self.user.id}\n")
        await self.change_presence(game=discord.Game(name="dp!help"))


loop = asyncio.get_event_loop()
loop.run_until_complete(run())