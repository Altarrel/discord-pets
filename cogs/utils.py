import json
import random
import discord
import math
import time

with open("./game_data/pets.json") as f:
    possible_pets = json.load(f)

def pick_new_pet():
    expansion, expansion_pets = random.choice(list(possible_pets.items()))
    pet = random.choice(list(expansion_pets.values()))
    pet["birth_time"] = (time.time() / 60)
    return (expansion, pet)

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
        1: "Youth",
        2: "Adolescent",
        3: "Adult",
        4: "Elderly"
    }
}

def convert(type, data):
    # data shouldn't be less than 0 or greater than 5
    # there are checks in the functions that raise and lower it
    to_int = int(data)
    converted = conversions[type][to_int]
    return converted

def create_stats_embed(author_name, profile):
    pet = json.loads(profile["pet"])
    graveyard = json.loads(profile["graveyard"])

    age = convert("age", pet["age"]) + f" {pet['age']}/4.0"
    saturation = convert("saturation", pet["saturation"]) + f" {pet['saturation']}/4.0"
    cleanliness = convert("cleanliness", pet["cleanliness"]) + f" {pet['cleanliness']}/4.0"
    health = convert("health", pet["health"]) + f" {pet['health']}/4.0"
    currency = profile["currency"]

    embed = discord.Embed(title=f"Pet and Stats for {author_name}")
    embed.set_thumbnail(url=pet["image"])
    embed.add_field(name="Name", value=pet["name"])
    embed.add_field(name="Expansion", value=pet["expansion"])
    embed.add_field(name="Nickname", value=pet["nickname"])
    embed.add_field(name="Age", value=age)
    embed.add_field(name="Saturation", value=saturation)
    embed.add_field(name="Cleanliness", value=cleanliness)
    embed.add_field(name="Health", value=health)

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(name="Currency", value=currency)
    embed.add_field(name="Pet Iteration", value=len(graveyard) + 1)

    return embed

def decay_stats(pet, current_time, last_interactions):
    # Times are in floored minutes
    fed_difference = current_time - last_interactions["fed"]
    cleaned_difference = current_time - last_interactions["cleaned"]

    # Less stat decay if they haven't been online in a while, maybe they were asleep
    if (fed_difference / 60) >= 4:
        # Reduce their stat by .1 for every 20 min since they have fed their pet
        subtract = .1 * int(fed_difference / 20)
        pet["saturation"] -= subtract
    else:
        # Reduce their stat by .1 for every 5 min since they have fed their pet
        subtract = .1 * int(fed_difference / 5)
        pet["saturation"] -= subtract

    if (cleaned_difference / 60) >= 4:
        subtract = .1 * int(cleaned_difference / 20)
        pet["cleanliness"] -= subtract
    else:
        subtract = .1 * int(cleaned_difference / 5)
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
