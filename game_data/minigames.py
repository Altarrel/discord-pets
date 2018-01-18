import asyncio
import random

import discord

async def coinflip(bot, ctx):
    await ctx.send(f"{ctx.author} | <:coinflip:403382619531902976> Guess whether the coin will land on heads or tails.")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ("h", "heads", "t", "tails")
    try:
        response = await bot.wait_for("message", check=check, timeout=20)
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author} | \U000023f0 You took too long to respond, you lose.")
        return

    flip = random.choice((("h", "heads"), ("t", "tails")))
    if not response.content.lower() in flip:
        await ctx.send(f"{ctx.author} | \U0001f626 You guessed incorrectly! The coin landed on {flip[1]}.")
        return

    winnings = random.randint(10, 15)
    await ctx.send(f"{ctx.author} | \U0001f389 You guessed correctly! The coin landed on {flip[1]}. You won {winnings} coins.")
    connection = await bot.db.acquire()
    async with connection.transaction():
        query = """UPDATE users SET currency = currency + $1 WHERE id = $2"""
        await connection.execute(query, winnings, ctx.author.id)
    await bot.db.release(connection)




# async def pick_the_toy(bot, ctx):
#     msg = await ctx.send(f"{ctx.author} | Choose a toy for your pet to play with.\n1. {}\n2. {}\n3. {}")
#     winnings = None
#     if not ctx.channel.permissions_for(ctx.author).add_reactions or not ctx.channel.permissions_for(bot.user).add_reactions:
#         await msg.edit(content=f"{ctx.author} | Choose a toy for your pet to play with.\n\n**Reactions failed, please send your answer. 1, 2, or 3?**")
#         use_msg = True

#     if use_msg:



async def dice(bot, ctx):
    await ctx.send(f"{ctx.author} | \U0001f3b2 Where do you think the die will land? Pick a number 1-6.")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content in ("1", "2", "3", "4", "5", "6")
    try:
        response = await bot.wait_for("message", check=check, timeout=20)
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author} | \U000023f0 You took too long to respond, you lose.")
        return

    roll = random.randint(1, 6)
    if roll != int(response.content):
        await ctx.send(f"{ctx.author} | \U0001f626 You guessed incorrectly! The die landed on {roll}.")
        return

    winnings = random.randint(20, 40)
    await ctx.send(f"{ctx.author} | \U0001f389 You guessed correctly! The die landed on {roll}. You won {winnings} coins.")
    connection = await bot.db.acquire()
    async with connection.transaction():
        query = """UPDATE users SET currency = currency + $1 WHERE id = $2;"""
        await connection.execute(query, winnings, ctx.author.id)
    await bot.db.release(connection)


    
all_minigames = (coinflip, dice)