import discord
from discord.ext import commands
import asyncpg


async def run():
    description = "A bot written in Python by Altarrel"
    pg = {"user": "postgres", "password": "discord-pets", "database": "PostgreSQL 10", "host": "127.0.0.1"}
    db_pool = await asyncpg.create_pool(*pg)
    db = await db_pool.aquire()

    bot = DiscordPets(description=description, db=db)
    try:
        await bot.start(config['token'])
    except KeyboardInterrupt:
        await db.close()
        await bot.logout()

class DiscordPets(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            description=kwargs.pop("description")
        )
        self.db = kwargs.pop("db")
        self.loop.create_task(self.load_all_extensions())
