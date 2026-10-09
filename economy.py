#!/usr/bin/env python3
"""
DeadsideBot Economy System
- Store with 20+ items
- Gambling (coinflip, dice)
- Crime system
- Currency earning from kills/deaths
"""

import json
import os
import random
from datetime import datetime

# Default store items (premium users can add custom items)
DEFAULT_STORE_ITEMS = {
    # Weapons
    "AK-47": {"price": 100, "category": "🔫 Weapons", "desc": "AK-47 assault rifle — the classic"},
    "M4A1": {"price": 100, "category": "🔫 Weapons", "desc": "M4A1 carbine — fast and deadly"},
    "Mosin": {"price": 80, "category": "🔫 Weapons", "desc": "Mosin bolt-action — sniper's dream"},
    "SKS": {"price": 75, "category": "🔫 Weapons", "desc": "SKS semi-auto — reliable mid-range"},
    "Shotgun": {"price": 60, "category": "🔫 Weapons", "desc": "Pump shotgun — close range monster"},
    "Pistol": {"price": 50, "category": "🔫 Weapons", "desc": "Standard pistol — backup weapon"},
    "VSS": {"price": 90, "category": "🔫 Weapons", "desc": "VSS suppressed sniper — stealth kills"},
    "SVD": {"price": 85, "category": "🔫 Weapons", "desc": "SVD Dragunov — designated marksman"},

    # Gear
    "Military Backpack": {"price": 80, "category": "🎒 Gear", "desc": "Large military backpack — max storage"},
    "Tactical Vest": {"price": 70, "category": "🎒 Gear", "desc": "Tactical plate carrier — extra slots"},

    # Medical
    "Medical Kit": {"price": 60, "category": "💉 Medical", "desc": "Full medical kit — heal everything"},
    "Bandages x10": {"price": 50, "category": "💉 Medical", "desc": "10 bandages — quick heals"},
    "Painkillers x5": {"price": 45, "category": "💊 Medical", "desc": "5 painkillers — restore health"},

    # Ammo
    "Ammo Crate": {"price": 50, "category": "📦 Ammo", "desc": "Mixed ammo crate — assorted rounds"},
    "AK Ammo x60": {"price": 50, "category": "📦 Ammo", "desc": "60 rounds 7.62x39mm"},
    "M4 Ammo x60": {"price": 50, "category": "📦 Ammo", "desc": "60 rounds 5.56x45mm"},
    "Sniper Ammo x20": {"price": 55, "category": "📦 Ammo", "desc": "20 rounds 7.62x54R — for Mosin/SVD"},

    # Armor
    "Helmet": {"price": 60, "category": "🛡️ Armor", "desc": "Ballistic helmet — head protection"},
    "Body Armor": {"price": 70, "category": "🛡️ Armor", "desc": "Level III body armor — full protection"},

    # Tools
    "Lockpick x5": {"price": 50, "category": "🔧 Tools", "desc": "5 lockpicks — open locked doors"},
    "Binoculars": {"price": 50, "category": "🔧 Tools", "desc": "Tactical binoculars — scout ahead"},

    # Supplies
    "Canned Food x10": {"price": 50, "category": "🥫 Supplies", "desc": "10 canned food — stay fed"},
    "Water Bottles x10": {"price": 50, "category": "🥫 Supplies", "desc": "10 water bottles — stay hydrated"},
}

# Crime outcomes — fun, random, with risk/reward
CRIME_OUTCOMES = [
    # Positive (70% chance)
    ("You robbed a trader and got away with it!", 50, 0.10),
    ("You stole from a military base — score!", 80, 0.08),
    ("You pickpocketed a survivor — nice haul!", 30, 0.15),
    ("You found an abandoned stash!", 60, 0.10),
    ("You raided a base and found some loot!", 70, 0.08),
    ("You mugged a trader — big risk, big reward!", 100, 0.05),
    ("You broke into a police station and found evidence!", 45, 0.12),
    ("You hijacked a supply truck!", 90, 0.06),
    ("You ambushed a patrol and took their gear!", 65, 0.08),
    ("You looted an airdrop before anyone noticed!", 75, 0.06),
    # Negative (30% chance)
    ("You got caught stealing and had to bribe your way out!", -25, 0.04),
    ("You tried to rob someone but they fought back!", -15, 0.06),
    ("You got shot while trying to steal! Ouch!", -40, 0.03),
    ("Your crime spree was interrupted by a patrol!", -20, 0.05),
    ("You tripped an alarm and had to flee empty-handed!", -10, 0.04),
    ("A sniper caught you mid-heist! Critically wounded!", -35, 0.03),
    ("You got ambushed while breaking in — lost everything!", -50, 0.02),
]

class Economy:
    def __init__(self, config):
        self.config = config
        self.store_items = dict(DEFAULT_STORE_ITEMS)

    def get_store_items(self):
        return self.store_items

    def find_item(self, name):
        """Find a store item by name (case-insensitive partial match)."""
        for store_name, info in self.store_items.items():
            if store_name.lower() == name.lower() or store_name.lower().startswith(name.lower()):
                return store_name, info
        return None, None

    def add_item(self, name, price, category, desc):
        """Add a custom item to the store (premium feature)."""
        self.store_items[name] = {"price": price, "category": category, "desc": desc}

    def gamble_coinflip(self, amount):
        """Gamble on a coin flip. 48% win chance, 2x payout."""
        result = random.choice(["heads", "tails"])
        if random.random() < 0.48:
            return True, amount * 2, f"🪙 Landed on **{result}** — you win! +{amount * 2} coins!"
        else:
            return False, 0, f"🪙 Landed on **{result}** — you lose! -{amount} coins."

    def gamble_dice(self, amount):
        """Gamble on a dice roll. Roll 4+ to win."""
        roll = random.randint(1, 6)
        if roll >= 6:
            return True, amount * 3, f"🎲 Rolled **{roll}** — JACKPOT! 3x! +{amount * 3} coins!"
        elif roll >= 5:
            return True, int(amount * 2.5), f"🎲 Rolled **{roll}** — Nice! 2.5x! +{int(amount * 2.5)} coins!"
        elif roll >= 4:
            return True, amount * 2, f"🎲 Rolled **{roll}** — Win! 2x! +{amount * 2} coins!"
        else:
            return False, 0, f"🎲 Rolled **{roll}** — You lose! -{amount} coins."

    def commit_crime(self):
        """Commit a crime. Returns (success, reward, message)."""
        # Weighted random selection
        outcomes = []
        for desc, reward, weight in CRIME_OUTCOMES:
            outcomes.extend([desc] * int(weight * 100))

        outcome_desc = random.choice(outcomes)
        # Find the reward for this outcome
        for desc, reward, _ in CRIME_OUTCOMES:
            if desc == outcome_desc:
                # Small chance of getting caught on positive outcomes
                if reward > 0 and random.random() < 0.30:
                    reward = -abs(reward) // 2
                    outcome_desc += " But you got caught escaping! Dropped some loot!"
                return reward > 0, reward, outcome_desc
        return False, 0, "Crime didn't work out."

    def calculate_kill_reward(self, kills, deaths, longest_kill_today, is_longest):
        """Calculate currency earned from kills."""
        config = self.config
        total = kills * config.get("currency_per_kill", 10)
        total += deaths * config.get("currency_per_death", 5)
        if is_longest:
            total += config.get("longest_kill_bonus", 50)
        return total
