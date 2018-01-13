import discord
from discord.ext import commands
import sys
import traceback

def setup(bot):
    bot._last_result = None
    bot.add_cog(Owner(bot))
    bot.add_cog(Eval(bot))

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
            await ctx.send("You must specify an extension to load.")
            return
        try:
            self.bot.load_extension(extension)
        except Exception as e:
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            print(f"Failed to load extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{extension} loaded.")

    @commands.command()
    async def unload(self, ctx, *, extension: str=None):
        """
        Unloads an extension/cog
        """

        if not extension:
            await ctx.send("You must specify an extension to unload.")
            return
        try:
            self.bot.unload_extension(extension)
        except Exception as e:
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            print(f"Failed to load extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{extension} unloaded.")

    @commands.command(name="reload")
    async def reload_(self, ctx, *, extension: str=None):
        """
        Reloads an extension/cog
        """

        if not extension:
            await ctx.send("You must specify an extension to reload.")
            return
        try:
            self.bot.unload_extension(extension)
            self.bot.load_extension(extension)
        except Exception as e:
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")
            print(f"Failed to reload extension: {extension}", file=sys.stderr)
            traceback.print_exc()
        else:
            await ctx.send(f"{extension} reloaded.")

    @commands.command()
    async def die(self, ctx):
        """
        Causes the bot to logout
        """

        await self.bot.db.close()
        await ctx.send("Database connection closed, logging out now.")
        await self.bot.logout()

    @commands.command()
    async def block(self, ctx, user: discord.User):
        """
        Prevents a user from using the bot
        """

        if user.id in self.bot.blocked:
            await ctx.send(f"{user} is already blocked, use {config.prefix}unblock <user> if you want to unblock them.")
            return

        self.bot.blocked.append(user.id)
        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """INSERT INTO blocked (id) VALUES ($1);"""
            await connection.execute(query, user.id)
        await self.bot.db.release(connection)

        await ctx.send(f"{user} was blocked.")

    @commands.command()
    async def unblock(self, ctx, user: discord.User):
        """
        Gives a user access to the bot again
        """

        if user.id in self.bot.blocked:
            await ctx.send(f"{user} isn't blocked, user {config.prefix}block <user> if you want to block them.")
            return

        self.bot.blocked.remove(user.id)
        connection = await self.bot.db.acquire()
        async with connection.transaction():
            query = """DELETE * FROM blocked WHERE id = $1"""
            await connection.execute(query, user.id)
        await self.bot.db.release(connection)

        await ctx.send(f"{user} was unblocked.")

class Eval:

    def __init__(self, bot):
        self.bot = bot

    def cleanup_code(self, content):
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(name='eval', hidden=True)
    @commands.is_owner()
    async def _eval(self, ctx, *, body: str):

        env = {
            'bot': ctx.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': ctx.bot._last_result,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        code = textwrap.indent(body, '  ')
        to_compile = f'async def func():\n{code}'

        try:
            exec(to_compile, env)
        except SyntaxError as e:
            return await ctx.send(self.get_syntax_error(e))

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('🔘')
            except:
                pass

            if ret is None:
                if value:
                    if len(value) > 2000:
                        gist = await self.bot.create_gist('Eval', [(f'eval.py', value)])
                        await ctx.send(gist)
                    else:
                        await ctx.send(f'```py\n{value}\n```')
            else:
                ctx.bot._last_result = ret
                fmt = f'{value}{ret}'

                if len(fmt) > 1989:  # len('```py\n\n```') == 10, one extra char for good measure
                    code = textwrap.dedent(fmt).replace('`', '\uFEFF')
                    gist = await self.bot.create_gist('Eval', [('eval.py', f'{code}')])
                    await ctx.send(f'**Eval was uploaded as a gist.**\n {gist}')
                else:
                    await ctx.send(f'```py\n{fmt}\n```')