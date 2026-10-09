#!/usr/bin/env python3
"""
DeadsideBot Channel Manager
- Auto-creates full channel structure on bot join
- Posts static content (rules, server info, store welcome)
- Manages channel references for background tasks
"""

import os
from datetime import datetime

# Channel structure to create
CHANNEL_STRUCTURE = {
    "categories": {
        "📺 INFORMATION": ["rules", "announcements", "server-info"],
        "💬 COMMUNITY": ["general", "introductions", "media"],
        "🎮 DEADSIDE": ["killfeed", "leaderboard", "server-stats", "connections"],
        "🛒 STORE": ["store", "tickets"],
        "🎲 ECONOMY": ["gamble", "crime", "balance"],
    },
    "rules_content": (
        "# 🎮 Server Rules\n\n"
        "## ⚔️ General Rules\n"
        "1. **Respect all players** — No harassment, racism, or toxic behavior\n"
        "2. **No cheating/exploiting** — Bugs, glitches, and hacks = permanent ban\n"
        "3. **No teaming in solo** — If the server is solo, play solo\n"
        "4. **Base raiding is allowed** — It's a PVP server, bases are fair game\n"
        "5. **No camping safe zones** — Don't camp traders or spawn points\n\n"
        "### 🛒 Store & Economy\n"
        "- Earn coins: **10 per kill**, **5 per death**, **50 longest kill bonus**, **20 daily**\n"
        "- Use `/store` to browse items, `/buy <item>` to purchase\n"
        "- Purchases create a ticket — an admin will fulfill your order in-game\n"
        "- Use `/gamble` and `/crime` for extra coins (with risk!)\n\n"
        "### 📊 Stats\n"
        "- Use `/stats` to check your kills, deaths, K/D, best weapon, longest kill\n"
        "- Use `/link <your_ingame_name>` to link your Discord to your Deadside character\n"
        "- Use `/leaderboard` to see the top killers\n\n"
        "### 🤖 Bot Commands\n"
        "`/stats` `/leaderboard` `/serverkd` `/globalkd` `/balance` `/link` `/daily`\n"
        "`/store` `/buy` `/gamble` `/crime` `/killfeed` `/streak` `/mastery`\n"
        "`/trade` `/raidalerts` `/event` `/achievements` `/bounty`\n\n"
        "---\n"
        "## 📜 Legal\n"
        "- **Terms of Service:** https://naterod23-lgtm.github.io/deadsidebot/TERMS_OF_SERVICE.html\n"
        "- **Privacy Policy:** https://naterod23-lgtm.github.io/deadsidebot/PRIVACY_POLICY.html\n\n"
        "---\n"
        "Powered by **DeadsideBot** 🤖"
    ),
    "server_info_content": (
        "# 📊 Server Information\n\n"
        "## 🤖 Bot Features\n"
        "- **Live Killfeed** — Real-time PvP kills with weapon and distance\n"
        "- **Player Stats** — K/D, best weapon, longest kill, kill streaks, weapon mastery\n"
        "- **Economy** — Earn coins from kills, spend in the store\n"
        "- **Store** — Buy in-game items with Discord coins\n"
        "- **Gambling** — Coinflip and dice\n"
        "- **Crime** — Risk/reward currency earning\n"
        "- **Leaderboard** — Auto-updating top killers\n"
        "- **Kill Streaks** — Track current and best streaks\n"
        "- **Raid Alerts** — Detects triple kills and rampages\n"
        "- **Seasonal Events** — Multiplier bonuses\n"
        "- **Achievements** — Unlock badges for milestones (Premium)\n"
        "- **Bounties** — Place bounties on players (Premium)\n\n"
        "## 🔗 Links\n"
        "- **Website:** https://naterod23-lgtm.github.io/deadsidebot/\n"
        "- **Terms of Service:** https://naterod23-lgtm.github.io/deadsidebot/TERMS_OF_SERVICE.html\n"
        "- **Privacy Policy:** https://naterod23-lgtm.github.io/deadsidebot/PRIVACY_POLICY.html\n"
        "- **GitHub:** https://github.com/naterod23-lgtm/deadsidebot\n\n"
        "---\n"
        "Powered by **DeadsideBot** 🤖"
    ),
    "store_welcome_content": (
        "# 🛒 Deadside Store\n\n"
        "Welcome to the store! Here's how it works:\n\n"
        "1. **Earn coins** by getting kills (10/kill), dying (5/death), daily bonus (20/day), or longest kill (50)\n"
        "2. **Browse items** with `/store`\n"
        "3. **Buy items** with `/buy <item> <quantity>` — this creates a private ticket\n"
        "4. **An admin** will fulfill your order in-game and mark it complete\n\n"
        "## 💰 Economy Rates\n"
        "- **10 coins** per kill\n"
        "- **5 coins** per death\n"
        "- **50 coins** for longest kill of the day\n"
        "- **20 coins** daily bonus (`/daily`)\n\n"
        "## 🎲 Risk vs Reward\n"
        "- `/gamble <amount> coinflip|dice` — Bet your coins\n"
        "- `/crime` — Commit crimes for coins (you might lose some!)\n\n"
        "---\n"
        "Click **Create Ticket** below to open a store order!"
    ),
}

class ChannelManager:
    def __init__(self, bot, data_path, log_dir):
        self.bot = bot
        self.data_path = data_path
        self.log_dir = log_dir

    def log(self, msg, level="INFO"):
        os.makedirs(self.log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line, flush=True)
        with open(os.path.join(self.log_dir, "deadsidebot.log"), "a") as f:
            f.write(line + "\n")

    async def setup_guild(self, guild, store_view_class):
        """Create the full channel structure for a guild."""
        self.log(f"Setting up channels for guild: {guild.name}")

        import json
        with open(self.data_path) as f:
            data = json.load(f)

        created = {}

        for cat_name, channel_names in CHANNEL_STRUCTURE["categories"].items():
            category = __import__('discord').utils.get(guild.categories, name=cat_name)
            if not category:
                category = await guild.create_category(cat_name)
                self.log(f"Created category: {cat_name}")

            for ch_name in channel_names:
                channel = __import__('discord').utils.get(guild.text_channels, name=ch_name)
                if not channel:
                    channel = await guild.create_text_channel(ch_name, category=category)
                    self.log(f"Created channel: #{ch_name} in {cat_name}")
                created[ch_name] = channel.id

        # Post static content
        discord_mod = __import__('discord')

        # Rules
        rules_ch = guild.get_channel(created.get("rules", 0))
        if rules_ch:
            try: await rules_ch.purge(limit=100)
            except: pass
            embed = discord_mod.Embed(title="📋 Server Rules", description=CHANNEL_STRUCTURE["rules_content"], color=discord_mod.Color.blue())
            await rules_ch.send(embed=embed)

        # Server Info
        info_ch = guild.get_channel(created.get("server-info", 0))
        if info_ch:
            try: await info_ch.purge(limit=100)
            except: pass
            embed = discord_mod.Embed(title="📊 Server Information", description=CHANNEL_STRUCTURE["server_info_content"], color=discord_mod.Color.green())
            await info_ch.send(embed=embed)

        # Store with Create Ticket button
        store_ch = guild.get_channel(created.get("store", 0))
        if store_ch:
            try: await store_ch.purge(limit=100)
            except: pass
            embed = discord_mod.Embed(title="🛒 Deadside Store", description=CHANNEL_STRUCTURE["store_welcome_content"], color=discord_mod.Color.orange())
            from economy import DEFAULT_STORE_ITEMS
            items_str = ""
            for name, info in list(DEFAULT_STORE_ITEMS.items())[:10]:
                items_str += f"• **{name}** — {info['price']}💰 ({info['desc']})\n"
            embed.add_field(name="Popular Items", value=items_str, inline=False)
            embed.set_footer(text="Use /store for full list, /buy <item> to purchase")
            view = store_view_class()
            await store_ch.send(embed=embed, view=view)

        # General welcome
        general_ch = guild.get_channel(created.get("general", 0))
        if general_ch:
            try: await general_ch.purge(limit=5)
            except: pass
            embed = discord_mod.Embed(
                title="🎉 Welcome!",
                description=(
                    "Welcome to the Deadside server!\n\n"
                    "**Get started:**\n"
                    "1. Read the rules in #rules\n"
                    "2. Use `/link <your_ingame_name>` to link your account\n"
                    "3. Check `/stats` for your kill stats\n"
                    "4. Visit #store to buy items with coins\n"
                    "5. Check #killfeed for live PvP kills\n\n"
                    "Enjoy your stay! 🔥"
                ),
                color=discord_mod.Color.purple()
            )
            await general_ch.send(embed=embed)

        # Save channel IDs
        data["channels_setup"][str(guild.id)] = created
        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

        self.log(f"Channel setup complete for {guild.name}")

    def get_channel(self, guild, channel_name):
        """Get a channel by name from a guild."""
        import json
        with open(self.data_path) as f:
            data = json.load(f)
        ch_id = data.get("channels_setup", {}).get(str(guild.id), {}).get(channel_name)
        if ch_id:
            return guild.get_channel(ch_id)
        import discord
        return discord.utils.get(guild.text_channels, name=channel_name)
