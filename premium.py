#!/usr/bin/env python3
"""
DeadsideBot Premium Features
- Achievement system
- Bounty system
- Multi-server support
- Custom branding
- Season resets
- Anti-cheat flags
"""

import json
import os
from datetime import datetime

class Premium:
    """Premium feature gate. Checks if a guild/server has premium enabled."""

    def __init__(self, config):
        self.config = config
        self.premium_key = config.get("premium_key", None)
        self.enabled = config.get("premium_enabled", False)

    def is_premium(self, guild_id=None):
        """Check if premium is enabled for a guild."""
        if not self.enabled:
            return False
        if not self.premium_key:
            return False
        # In production, this would verify the premium key against a licensing server
        # For now, just check the flag
        return True

    def enable_premium(self, key):
        """Enable premium with a valid key."""
        # In production, verify key against licensing server
        if key and len(key) > 10:
            self.config["premium_enabled"] = True
            self.config["premium_key"] = key
            self.enabled = True
            return True
        return False

    # --- Achievement System ---
    ACHIEVEMENTS = {
        "first_blood": {"name": "🩸 First Blood", "desc": "Get your first kill"},
        "killer": {"name": "💀 Killer", "desc": "Reach 10 kills"},
        "serial_killer": {"name": "🔪 Serial Killer", "desc": "Reach 50 kills"},
        "legend": {"name": "🏆 Legend", "desc": "Reach 100 kills"},
        "marksman": {"name": "🎯 Marksman", "desc": "Get a 200m+ kill"},
        "sniper": {"name": "🎯 Sniper", "desc": "Get a 400m+ kill"},
        "god_sniper": {"name": "🌟 God Sniper", "desc": "Get a 500m+ kill"},
        "survivor": {"name": "🛡️ Survivor", "desc": "Die 10 times (and keep going)"},
        "unstoppable": {"name": "⚡ Unstoppable", "desc": "5 kills without dying"},
        "weapon_master": {"name": "🔫 Weapon Master", "desc": "Get kills with 5+ different weapons"},
    }

    def get_achievement_embed(self, player_name, achievements):
        """Create an embed showing a player's achievements."""
        import discord
        embed = discord.Embed(
            title=f"🏆 Achievements — {player_name}",
            color=discord.Color.gold()
        )
        if not achievements:
            embed.description = "No achievements unlocked yet. Get some kills!"
            return embed

        unlocked = 0
        for ach_id, ach in self.ACHIEVEMENTS.items():
            if ach_id in achievements:
                embed.add_field(name=f"✅ {ach['name']}", value=ach["desc"], inline=False)
                unlocked += 1
            else:
                embed.add_field(name=f"🔒 {ach['name']}", value=ach["desc"], inline=False)

        embed.set_footer(text=f"{unlocked}/{len(self.ACHIEVEMENTS)} unlocked • DeadsideBot Premium")
        return embed

    # --- Bounty System ---
    def place_bounty(self, data, target_name, reward, placed_by):
        """Place a bounty on a player."""
        bounties = data.setdefault("bounties", [])
        bounty = {
            "id": len(bounties) + 1,
            "target": target_name,
            "reward": reward,
            "placed_by": placed_by,
            "placed_at": datetime.now().isoformat(),
            "status": "active",
            "claimed_by": None,
            "claimed_at": None,
        }
        bounties.append(bounty)
        return bounty

    def get_active_bounties(self, data):
        """Get all active bounties."""
        return [b for b in data.get("bounties", []) if b["status"] == "active"]

    def claim_bounty(self, data, target_name, claimed_by):
        """Claim a bounty when the target is killed."""
        for b in data.get("bounties", []):
            if b["target"].lower() == target_name.lower() and b["status"] == "active":
                b["status"] = "claimed"
                b["claimed_by"] = claimed_by
                b["claimed_at"] = datetime.now().isoformat()
                return b
        return None

    # --- Anti-Cheat Detection ---
    def detect_suspicious(self, kill):
        """Detect suspicious kill patterns."""
        flags = []
        # Impossible distance check (over 1000m is very suspicious in Deadside)
        if kill.get("distance", 0) > 1000:
            flags.append(f"⚠️ Impossible distance: {kill['distance']}m by {kill.get('killer_name')}")
        # Very high kill rate would be checked here too
        return flags
