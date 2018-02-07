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
            command_prefix=commands.when_mentioned_or(config.prefix),
            game=discord.Game(name=f"{config.prefix}help")
        )

        # Get rid of default help command so I can replace it with my trash one
        self.remove_command("help")
        self.last_interactions = {}
        self.db = kwargs.pop("db")
        self.blocked = kwargs.pop("blocked")
        self.loop.create_task(self.load_all_extensions())

        self.loop.create_task(self.update_guild_count())

    async def on_message(self, message):
        await self.wait_until_ready()
        # Stop certain users and bots from using the bot
        if message.author.bot or message.author.id in self.blocked:
            return
            
        await self.process_commands(message)

    # Post guild count to https://discordbots.org/

    async def on_ready(self):
        print(f"Username: {self.user.name}\n"
              f"ID: {self.user.id}\n")

    async def update_guild_count(self):
        await self.wait_until_ready()
        await asyncio.sleep(1)
        while not self.is_closed():
            if self.user.id in config.TEST_IDS:
                print("Logged in under a TEST_ID, not posting guild count to discord bot list.")
                return

            headers = {'Authorization': config.DBL_TOKEN}
            data = {'server_count': len(self.guilds)}
            api_url = 'https://discordbots.org/api/bots/' + str(self.user.id) + '/stats'
            async with aiohttp.ClientSession() as session:
                await session.post(api_url, data=data, headers=headers)
            print("Posted guild count to discord bot list")

            await asyncio.sleep(600)

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
