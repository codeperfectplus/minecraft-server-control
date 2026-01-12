import random
import re

def generate_gamer_tag():
    """Generate a unique gamer tag based on the username."""
    adjectives = ['Swift', 'Bold', 'Silent', 'Cosmic', 'Wild', 'Neon', 'Pixel', 'Blocky', 'Ender', 'Nether']
    nouns = ['Steve', 'Alex', 'Creeper', 'Miner', 'Crafter', 'Knight', 'Dragon', 'Wolf', 'Ghast', 'Warden']
    gamer_tag = f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(100, 999)}"

    return gamer_tag
