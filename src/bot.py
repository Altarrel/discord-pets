import traceback

import discord
from discord.ext import commands

class DiscordPets(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.prefix)
            game=discord.Game(name=f"{config.prefix}help")
        )

    async def on_ready(self):
        print(f"Username: {self.user.name}\n"
              f"ID: {self.user.id}\n")

    async def load_all_extensions(self):
        await self.wait_until_ready()
        extensions = ()
        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception:
                print(f"Failed to load extension {extension}." file=sys.stderr)
                traceback.print_exc()
