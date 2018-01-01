import discord
import asyncio
import random

async def coinflip(bot, ctx):
    msg = await ctx.send("Guess whether the coin will land on heads or tails.")
    use_msg = False
    winnings = None
    if ctx.channel.permissions_for(ctx.author).add_reactions:
        try:
            await msg.add_reaction("\U0001f1ed")
            await msg.add_reaction("\U0001f1f9")
        except discord.Forbidden:
            await msg.edit(content="Guess whether the coin will land on heads or tails.\n\n**I don't have add_reactions permissions, say h/heads or t/tails.**")
            use_msg = True
    else:
        use_msg = True

    if use_msg:
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ("h", "heads", "t", "tails")
        try:
            guess = await bot.wait_for("message", check=check, timeout=20)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond, you lose.")
            return

        answer = random.choice((("h", "heads"), ("t", "tails")))
        if guess.content.lower() in answer:
            winnings = random.randint(5, 20)
            await ctx.send(f"\U0001f389 You won {winnings} pet coins! The coin landed on {answer[1]}. \U0001f389")
        else:
            await ctx.send(f"You didn't guess correctly! The coin landed on {answer[1]}. \U0001f626")
    else:
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ("\U0001f1ed", "\U0001f1f9")
        try:
            guess = await bot.wait_for("reaction_add", check=check, timeout=20)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond, you lose.")
            return

        answer = random.choice(("\U0001f1ed", "\U0001f1f9"))
        if str(guess[0].emoji) == answer:
            winnings = random.randint(5, 20)
            await ctx.send(f"\U0001f389 You won {winnings} pet coins! The coin landed on {answer[1]}. \U0001f389")
        else:
            await ctx.send(f"You didn't guess correctly! The coin landed on {answer[1]}. \U0001f626")

    if winnings:
        connection = await bot.db.acquire()
        async with connection.transaction():
            query = """UPDATE users SET currency = currency + $1 WHERE id = $2;"""
            await connection.execute(query, winnings, ctx.author.id)
        await bot.db.release(connection)

all_minigames = (coinflip,)