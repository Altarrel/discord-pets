import random
import copy
import json
import time

import discord


with open("./game_data/pets.json") as f:
    all_pets = json.load(f)

async def get_profile(bot, user_id):
    query = """SELECT * FROM users WHERE id = $1"""
    profile = await bot.db.fetchrow(query, user_id)
    return profile


def pick_new_pet(previous_pet):
    modified_pets = copy.copy(all_pets)

    if previous_pet:
        # Modify all_pets to prevent the user from getting the same pet 2 times in a row.
        del modified_pets[previous_pet["expansion"]][previous_pet["name"]]

    expansion, expansion_pets = random.choice(list(modified_pets.items()))
    pet = random.choice(list(expansion_pets.values()))
    pet["birth_time"] = (time.time() / 60)
    return expansion, pet

conversions = {
    "saturation": {
        0: "Could eat a horse",
        1: "Hungry",
        2: "Nibbling",
        3: "Satisfied",
        4: "Full"
    },
    "happiness": {
        0: "Miserable",
        1: "Down",
        2: "So so",
        3: "Content",
        4: "Chirpy"
    },
    "health": {
        0: "Feeble",
        1: "Sick",
        2: "Under the weather",
        3: "Fit",
        4: "Full of life"
    },
    "cleanliness": {
        0: "Filthy",
        1: "Dusty",
        2: "Unkempt",
        3: "Groomed",
        4: "Spotless"
    },
    "age": {
        0: "Newborn",
        1: "Adolescent",
        2: "Adult",
        3: "Elderly",
        4: "Dead"
    }
}


def convert(type, data):
    # data shouldn't be less than 0 or greater than 5
    # there are checks in the functions that raise and lower it
    rounded = int(data / 10)
    converted = conversions[type][rounded]
    return converted


def age_convert(age):
    text = ""
    if 0 <= age < 2:
        text = "Newborn"
    elif 2 < age < 6:
        text = "Adolescent"
    elif 6 < age < 10:
        text = "Adult"
    elif 10 < age < 14:
        text = "Elderly"
    elif age >= 14:
        text = "Dead"
    return text


def create_stats_embed(author_name, profile):
    pet = json.loads(profile["pet"])
    graveyard = json.loads(profile["graveyard"])

    age = age_convert(pet["age"]) + f" {pet['age']}/14"
    saturation = convert("saturation", pet["saturation"]) + f" {pet['saturation']}/40"
    cleanliness = convert("cleanliness", pet["cleanliness"]) + f" {pet['cleanliness']}/40"
    health = convert("health", pet["health"]) + f" {pet['health']}/40"
    currency = profile["currency"]

    embed = discord.Embed(title=f"Pet and Stats for {author_name}")
    embed.set_thumbnail(url=pet["image"])
    embed.add_field(name="Name", value=pet["name"])
    embed.add_field(name="Expansion", value=pet["expansion"])
    embed.add_field(name="Nickname", value=pet["nickname"])
    embed.add_field(name="Age", value=age)

    # Alive check
    if pet["health"] > 0 and pet["age"] < 14:
        embed.add_field(name="Saturation", value=saturation)
        embed.add_field(name="Cleanliness", value=cleanliness)
        embed.add_field(name="Health", value=health)
    else:
        embed.add_field(name="Dead", value="Your pet is dead.", inline=False)

    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(name="Currency", value=currency)
    embed.add_field(name="Pet Iteration", value=len(graveyard) + 1)

    return embed


def decay_stat(pet, stat_type, current_time, last_interactions):
    # Times are in floored minutes
    difference = current_time - last_interactions[stat_type]

    # Less stat decay if they haven't been online in a while, maybe they were asleep
    if (difference / 60) >= 4:
        # Reduce their stat by 1 for every 30 min since they have fed their pet
        subtract = int(difference / 30)
        pet[stat_type] -= subtract
    else:
        # Reduce their stat by 1 for every 10 min since they have fed their pet
        subtract = int(difference / 10)
        pet[stat_type] -= subtract

    # If stat become negative, remove the amount less than 0 from health
    if pet[stat_type] < 0:
        pet["health"] += pet[stat_type]

    # Set all stats to 0 so they don't stay negative
    if pet[stat_type] < 0:
        pet[stat_type] = 0

    return pet


def decay_stats(pet, current_time, last_interactions):
    # Times are in floored minutes
    fed_difference = current_time - last_interactions["saturation"]
    cleaned_difference = current_time - last_interactions["cleanliness"]

    # age_difference will be in floored days
    age_days = int((current_time - pet["birth_time"]) / 1440)
    pet["age"] = age_days

    # Less stat decay if they haven't been online in a while, maybe they were asleep
    if (fed_difference / 60) >= 4:
        # Reduce their stat by 1 for every 30 min since they have fed their pet
        subtract = int(fed_difference / 30)
        pet["saturation"] -= subtract
    else:
        # Reduce their stat by 1 for every 10 min since they have fed their pet
        subtract = int(fed_difference / 10)
        pet["saturation"] -= subtract

    if (cleaned_difference / 60) >= 4:
        subtract = int(cleaned_difference / 30)
        pet["cleanliness"] -= subtract
    else:
        subtract = int(cleaned_difference / 10)
        pet["cleanliness"] -= subtract

    # If stats become negative, remove the amount less than 0 from health
    if pet["saturation"] < 0:
        pet["health"] += pet["saturation"]
    if pet["cleanliness"] < 0:
        pet["health"] += pet["cleanliness"]

    # Set all stats to 0 so they don't stay negative
    if pet["health"] < 0:
        pet["health"] = 0
    if pet["saturation"] < 0:
        pet["saturation"] = 0
    if pet["cleanliness"] < 0:
        pet["cleanliness"] = 0
        
    return pet


def possessive(name):
    return name + ("'" if name.endswith("s") else "'s")


def a_or_an(text):
    vowels = ("a", "e", "i", "o", "u", "A", "E", "I", "O", "U")
    return "an" if text[0] in vowels and text != "user" else "a"
