#!/usr/bin/env python3
"""
DeadsideBot — The All-in-One Discord Bot for Deadside Servers
Features: Killfeed, Stats, Economy, Store, Gambling, Crime, Achievements, more.

Setup:
  1. pip3 install --break-system-packages discord.py paramiko
  2. Create a Discord bot at discord.com/developers/applications
  3. Enable Privileged Gateway Intents (Server Members + Message Content)
  4. Edit config.json with your bot token and SFTP details
  5. Run: python3 bot.py
  6. Invite the bot to your server with Administrator permissions
"""

import json
import os
import sys
import time
import random
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

# Import our modules
from config import load_config
from stats import StatsEngine
from economy import Economy
from channels import ChannelManager
from tickets import StoreTicketView, TicketOrderView, FulfillView
from premium import Premium
from tasks import BotTasks

# ============================================================
# SETUP
# ============================================================
config = load_config()
stats_engine = StatsEngine(config)
economy = Economy(config)
premium = Premium(config)

# Ensure data file exists
data_path = config.get("data_path", "/opt/deadsidebot/data/deadside_data.json")
os.makedirs(os.path.dirname(data_path), exist_ok=True)
if not os.path.exists(data_path):
    with open(data_path, "w") as f:
        json.dump({
            "players": {}, "stats": {}, "tickets": [],
            "last_log_position": 0, "longest_kill_today": {},
            "processed_kill_ids": [], "recent_kills": [],
            "channels_setup": {}, "achievements": {}, "bounties": [],
        }, f, indent=2)

channel_manager = ChannelManager(None, data_path, config.get("log_dir", "/opt/deadsidebot/logs"))

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
channel_manager.bot = bot

# ============================================================
# EVENTS
# ============================================================
@bot.event
async def on_ready():
    stats_engine.log(f"DeadsideBot online as {bot.user} (ID: {bot.user.id})")
    print(f"\n✅ Bot connected! Logged in as {bot.user}")
    print(f"   ID: {bot.user.id}")
    print(f"   Servers: {len(bot.guilds)}")

    try:
        synced = await bot.tree.sync()
        stats_engine.log(f"Synced {len(synced)} slash commands")
        print(f"   Slash commands: {len(synced)}")
    except Exception as e:
        stats_engine.log(f"Failed to sync commands: {e}", "ERROR")

    # Setup channels for each guild
    for guild in bot.guilds:
        await channel_manager.setup_guild(guild, StoreTicketView)

    # Start background tasks
    bot_tasks = BotTasks(bot, stats_engine, channel_manager, config)
    await bot_tasks.start_all()
    stats_engine.log("Background tasks started")

@bot.event
async def on_guild_join(guild):
    stats_engine.log(f"Joined new guild: {guild.name} ({guild.id})")
    await channel_manager.setup_guild(guild, StoreTicketView)

@bot.event
async def on_member_join(member):
    """Welcome new members and assign Deadside role."""
    guild = member.guild
    
    # Auto-assign the Deadside role
    deadside_role = discord.utils.get(guild.roles, name="Deadside")
    if deadside_role:
        try:
            await member.add_roles(deadside_role)
            stats_engine.log(f"Assigned Deadside role to {member.name}")
        except Exception as e:
            stats_engine.log(f"Failed to assign Deadside role to {member.name}: {e}", "WARN")
    
    # Welcome message
    ch = channel_manager.get_channel(guild, "general")
    if ch:
        welcomes = [
            f"Yo {member.mention}! Welcome to TBS PVP! 🔥 Grab a seat and let's get some kills!",
            f"What's good {member.mention}! Welcome to the crew! 💀 Read #rules to get started!",
            f"{member.mention} just dropped in! Welcome! ⚔️ Use `/link` to link your IGN!",
            f"Welcome {member.mention}! 🎮 Check #store to buy items with coins you earn from kills!",
            f"{member.mention} has entered the wasteland! 🔥 Search **TBS_PVP** in Deadside Private Servers to join!",
        ]
        try:
            await ch.send(random.choice(welcomes))
        except:
            pass

# ============================================================
# SLASH COMMANDS
# ============================================================

# --- Stats Commands ---

@bot.tree.command(name="stats", description="📊 Check player stats (kills, deaths, K/D, best weapon, longest kill)")
@app_commands.describe(player="Optional: check another player's stats by in-game name")
async def cmd_stats(interaction: discord.Interaction, player: str = None):
    if player is None:
        data = stats_engine.load_data()
        user_data = data["players"].get(str(interaction.user.id))
        if not user_data or not user_data.get("linked_name"):
            await interaction.response.send_message(
                "You haven't linked your in-game name! Use `/link <your_deadside_name>` first.",
                ephemeral=True
            )
            return
        player = user_data["linked_name"]

    stats = stats_engine.get_player_stats(player)
    if not stats:
        await interaction.response.send_message(
            f"No stats found for '{player}'. Get some kills first! 💀",
            ephemeral=True
        )
        return

    kills = stats["kills"]
    deaths = stats["deaths"]
    kd = kills / deaths if deaths > 0 else kills
    best_weapon = max(stats["weapons"].items(), key=lambda x: x[1]) if stats["weapons"] else ("None", 0)

    embed = discord.Embed(title=f"📊 Stats — {player}", color=discord.Color.blue())
    embed.add_field(name="Kills", value=str(kills), inline=True)
    embed.add_field(name="Deaths", value=str(deaths), inline=True)
    embed.add_field(name="K/D Ratio", value=f"{kd:.2f}", inline=True)
    embed.add_field(name="Best Weapon", value=f"{best_weapon[0]} ({best_weapon[1]} kills)", inline=False)
    embed.add_field(name="Longest Kill", value=f"{stats['longest_kill']}m with {stats['longest_kill_weapon'] or 'N/A'}", inline=False)

    data = stats_engine.load_data()
    lkd = data.get("longest_kill_today", {})
    if lkd.get("player", "").lower() == player.lower():
        embed.add_field(name="🏆 Longest Kill Today", value=f"{lkd['distance']}m with {lkd['weapon']}", inline=False)

    # Show achievements if premium
    if premium.is_premium():
        achs = stats_engine.get_achievements(player)
        if achs:
            ach_names = [premium.ACHIEVEMENTS[a]["name"] for a in achs if a in premium.ACHIEVEMENTS]
            embed.add_field(name="🏆 Achievements", value=" ".join(ach_names[:10]) or "None", inline=False)

    embed.set_footer(text="DeadsideBot • Stats")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="🏆 Show top killers on the server")
async def cmd_leaderboard(interaction: discord.Interaction):
    leaderboard = stats_engine.get_leaderboard(10)
    if not leaderboard:
        await interaction.response.send_message("No kills recorded yet! 💀", ephemeral=True)
        return

    embed = discord.Embed(title="🏆 Top Killers", color=discord.Color.gold())
    for i, (name, s) in enumerate(leaderboard):
        kd = s["kills"] / s["deaths"] if s["deaths"] > 0 else s["kills"]
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
        embed.add_field(
            name=f"{medal} {name}",
            value=f"K: {s['kills']} | D: {s['deaths']} | K/D: {kd:.2f} | Longest: {s['longest_kill']}m",
            inline=False
        )
    embed.set_footer(text="DeadsideBot • Leaderboard")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverkd", description="📈 Show server-wide K/D statistics")
async def cmd_serverkd(interaction: discord.Interaction):
    server_stats = stats_engine.get_server_stats()
    if not server_stats:
        await interaction.response.send_message("No stats recorded yet!", ephemeral=True)
        return

    embed = discord.Embed(title="📈 Server K/D Stats", color=discord.Color.purple())
    embed.add_field(name="Total Kills", value=str(server_stats["total_kills"]), inline=True)
    embed.add_field(name="Total Deaths", value=str(server_stats["total_deaths"]), inline=True)
    embed.add_field(name="Avg K/D", value=f"{server_stats['avg_kd']:.2f}", inline=True)
    embed.add_field(name="Active Players", value=str(server_stats["active_players"]), inline=True)
    embed.add_field(name="Top Weapon", value=f"{server_stats['top_weapon'][0]} ({server_stats['top_weapon'][1]} kills)", inline=True)
    embed.add_field(name="Longest Kill", value=f"{server_stats['longest_kill']}m", inline=False)

    data = stats_engine.load_data()
    lkd = data.get("longest_kill_today", {})
    if lkd.get("player"):
        embed.add_field(name="🏆 Longest Kill Today", value=f"{lkd['player']} — {lkd['distance']}m ({lkd['weapon']})", inline=False)

    embed.set_footer(text="DeadsideBot • Server Stats")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="globalkd", description="🌍 Show your global K/D across all sessions")
async def cmd_globalkd(interaction: discord.Interaction):
    data = stats_engine.load_data()
    user_data = data["players"].get(str(interaction.user.id))
    if not user_data or not user_data.get("linked_name"):
        await interaction.response.send_message("Link your account first with `/link <name>`!", ephemeral=True)
        return

    name = user_data["linked_name"]
    stats = data["stats"].get(name, {})
    kills = stats.get("kills", 0)
    deaths = stats.get("deaths", 0)
    kd = kills / deaths if deaths > 0 else kills

    embed = discord.Embed(title=f"🌍 Global K/D — {name}", color=discord.Color.green())
    embed.add_field(name="Kills", value=str(kills), inline=True)
    embed.add_field(name="Deaths", value=str(deaths), inline=True)
    embed.add_field(name="K/D", value=f"{kd:.2f}", inline=True)
    embed.add_field(name="Currency", value=f"{user_data['balance']} 💰", inline=False)
    embed.set_footer(text="DeadsideBot • Global Stats")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="killfeed", description="💀 Show recent PvP kills")
async def cmd_killfeed(interaction: discord.Interaction):
    recent = stats_engine.get_recent_kills(10)
    if not recent:
        await interaction.response.send_message("No kills recorded yet! 💀", ephemeral=True)
        return

    embed = discord.Embed(title="💀 Recent Kill Feed", color=discord.Color.red())
    for kill in recent:
        embed.add_field(
            name=f"☠️ {kill['killer_name']} ➜ {kill['victim_name']}",
            value=f"Weapon: {kill['weapon']} | Distance: {kill['distance']}m",
            inline=False
        )
    embed.set_footer(text="DeadsideBot • Kill Feed")
    await interaction.response.send_message(embed=embed)

# --- Economy Commands ---

@bot.tree.command(name="balance", description="💰 Check your Deadside Coins balance")
async def cmd_balance(interaction: discord.Interaction):
    data = stats_engine.load_data()
    player = stats_engine.get_or_create_player(interaction.user.id, interaction.user.name)
    stats_engine.save_data(data)

    embed = discord.Embed(title="💰 Your Balance", description=f"**{player['balance']}** Deadside Coins", color=discord.Color.gold())
    if player.get("linked_name"):
        embed.add_field(name="Linked IGN", value=player["linked_name"], inline=True)
    else:
        embed.add_field(name="Linked IGN", value="Not linked — use `/link <name>`", inline=True)
    embed.set_footer(text="Earn coins from kills! Visit #store to spend them.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="link", description="🔗 Link your Discord to your Deadside in-game name")
@app_commands.describe(name="Your Deadside in-game player name")
async def cmd_link(interaction: discord.Interaction, name: str):
    data = stats_engine.load_data()
    player = stats_engine.get_or_create_player(interaction.user.id, interaction.user.name)
    player["linked_name"] = name
    stats_engine.save_data(data)
    await interaction.response.send_message(
        f"✅ Linked to Deadside player **{name}**!\n"
        f"You'll earn {config.get('currency_per_kill', 10)}💰/kill, {config.get('currency_per_death', 5)}💰/death.",
        ephemeral=True
    )
    stats_engine.log(f"User {interaction.user.name} linked to {name}")

@bot.tree.command(name="daily", description="🎁 Claim your daily currency bonus (20 coins)")
async def cmd_daily(interaction: discord.Interaction):
    data = stats_engine.load_data()
    player = stats_engine.get_or_create_player(interaction.user.id, interaction.user.name)
    today = datetime.now().strftime("%Y-%m-%d")
    if player.get("daily_last") == today:
        await interaction.response.send_message("Already claimed today! Come back tomorrow. 🕐", ephemeral=True)
        return
    player["balance"] += config.get("daily_bonus", 20)
    player["daily_last"] = today
    stats_engine.save_data(data)
    await interaction.response.send_message(f"✅ Claimed **{config.get('daily_bonus', 20)}** coins! Balance: **{player['balance']}** 💰", ephemeral=True)

@bot.tree.command(name="store", description="🛒 Browse the store — buy items with your coins")
async def cmd_store(interaction: discord.Interaction):
    items = economy.get_store_items()
    embed = discord.Embed(
        title="🛒 Deadside Store",
        description=(
            f"Use `/buy <item> <qty>` to purchase.\n"
            f"Earn: {config.get('currency_per_kill', 10)}/kill, {config.get('currency_per_death', 5)}/death, "
            f"{config.get('daily_bonus', 20)}/daily, {config.get('longest_kill_bonus', 50)} longest kill"
        ),
        color=discord.Color.orange()
    )
    categories = {}
    for name, info in items.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((name, info))

    for cat, cat_items in categories.items():
        lines = [f"**{n}** — {i['price']}💰 | {i['desc']}" for n, i in cat_items]
        embed.add_field(name=cat, value="\n".join(lines), inline=False)

    embed.set_footer(text="DeadsideBot • Store")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="buy", description="🛒 Buy an item (creates a ticket for admin fulfillment)")
@app_commands.describe(item="Item name from the store", quantity="How many (default: 1)")
async def cmd_buy(interaction: discord.Interaction, item: str, quantity: int = 1):
    data = stats_engine.load_data()
    player = stats_engine.get_or_create_player(interaction.user.id, interaction.user.name)

    item_name, item_info = economy.find_item(item)
    if not item_name:
        await interaction.response.send_message(f"❌ '{item}' not found! Use `/store` to see items.", ephemeral=True)
        return

    total_cost = item_info["price"] * quantity
    if player["balance"] < total_cost:
        await interaction.response.send_message(
            f"❌ Need {total_cost}💰, have {player['balance']}💰! Earn more with kills, /daily, or /crime!",
            ephemeral=True
        )
        return

    player["balance"] -= total_cost

    # Find or create an open ticket
    ticket = None
    for t in data.get("tickets", []):
        if t["user_id"] == str(interaction.user.id) and t["status"] == "open":
            ticket = t
            break
    if not ticket:
        ticket_id = len(data.get("tickets", [])) + 1
        ticket = {
            "id": ticket_id, "user_id": str(interaction.user.id), "user_name": interaction.user.name,
            "linked_name": player.get("linked_name", "NOT LINKED"), "status": "open",
            "created_at": datetime.now().isoformat(), "channel_id": None, "items": []
        }
        data.setdefault("tickets", []).append(ticket)

    ticket["items"].append({"name": item_name, "qty": quantity, "cost": total_cost})
    stats_engine.save_data(data)

    await interaction.response.send_message(
        f"✅ Added **{quantity}x {item_name}** ({total_cost}💰) to your order!\n"
        f"Balance: **{player['balance']}**💰\n"
        f"Visit #store and click 'Create Ticket' to submit your order.",
        ephemeral=True
    )

@bot.tree.command(name="gamble", description="🎲 Gamble your coins — coinflip or dice")
@app_commands.describe(amount="How many coins to bet", game="coinflip or dice (default: coinflip)")
@app_commands.choices(game=[
    app_commands.Choice(name="coinflip", value="coinflip"),
    app_commands.Choice(name="dice", value="dice"),
])
async def cmd_gamble(interaction: discord.Interaction, amount: int, game: str = "coinflip"):
    if amount <= 0:
        await interaction.response.send_message("❌ Can't bet 0 or negative!", ephemeral=True)
        return
    data = stats_engine.load_data()
    player = stats_engine.get_or_create_player(interaction.user.id, interaction.user.name)
    if player["balance"] < amount:
        await interaction.response.send_message(f"❌ Only have {player['balance']}💰, can't bet {amount}!", ephemeral=True)
        return

    if game == "coinflip":
        player["balance"] -= amount
        success, winnings, msg = economy.gamble_coinflip(amount)
        if success:
            player["balance"] += winnings
        stats_engine.save_data(data)
        await interaction.response.send_message(f"{msg}\nBalance: {player['balance']}💰")
    else:
        player["balance"] -= amount
        success, winnings, msg = economy.gamble_dice(amount)
        if success:
            player["balance"] += winnings
        stats_engine.save_data(data)
        await interaction.response.send_message(f"{msg}\nBalance: {player['balance']}💰")

@bot.tree.command(name="crime", description="🦹 Commit a crime for coins (risky!)")
async def cmd_crime(interaction: discord.Interaction):
    data = stats_engine.load_data()
    player = stats_engine.get_or_create_player(interaction.user.id, interaction.user.name)

    success, reward, msg = economy.commit_crime()
    player["balance"] += reward
    if player["balance"] < 0:
        player["balance"] = 0
    stats_engine.save_data(data)

    emoji = "🤑" if reward > 0 else "🚔"
    color = discord.Color.green() if reward > 0 else discord.Color.red()
    embed = discord.Embed(
        title=f"{emoji} Crime Result",
        description=f"{msg}\n\n{'+' if reward > 0 else ''}{reward}💰 | Balance: {player['balance']}💰",
        color=color
    )
    embed.set_footer(text="DeadsideBot • /crime has risks!")
    await interaction.response.send_message(embed=embed)

# --- Premium Commands ---

@bot.tree.command(name="achievements", description="🏆 Show your achievements (Premium)")
async def cmd_achievements(interaction: discord.Interaction):
    if not premium.is_premium():
        await interaction.response.send_message(
            "⭐ **Premium Feature** — Achievements are available with DeadsideBot Premium!\n"
            "Upgrade to unlock: achievements, bounties, multi-server, custom branding, and more!",
            ephemeral=True
        )
        return

    data = stats_engine.load_data()
    user_data = data["players"].get(str(interaction.user.id))
    if not user_data or not user_data.get("linked_name"):
        await interaction.response.send_message("Link your account first with `/link <name>`!", ephemeral=True)
        return

    name = user_data["linked_name"]
    achievements = stats_engine.get_achievements(name)
    embed = premium.get_achievement_embed(name, achievements)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="bounty", description="🎯 Place a bounty on a player (Premium)")
@app_commands.describe(target="Player to place a bounty on", reward="Coin reward for the bounty")
async def cmd_bounty(interaction: discord.Interaction, target: str, reward: int):
    if not premium.is_premium():
        await interaction.response.send_message("⭐ **Premium Feature** — Bounties require DeadsideBot Premium!", ephemeral=True)
        return

    data = stats_engine.load_data()
    player = stats_engine.get_or_create_player(interaction.user.id, interaction.user.name)
    if player["balance"] < reward:
        await interaction.response.send_message(f"❌ You need {reward}💰 but only have {player['balance']}💰!", ephemeral=True)
        return

    player["balance"] -= reward
    bounty = premium.place_bounty(data, target, reward, interaction.user.name)
    stats_engine.save_data(data)

    embed = discord.Embed(
        title=f"🎯 Bounty Placed — #{bounty['id']}",
        description=f"**Target:** {target}\n**Reward:** {reward}💰\n**Placed by:** {interaction.user.mention}",
        color=discord.Color.red()
    )
    embed.set_footer(text="DeadsideBot Premium • Bounty System")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setupchannels", description="🔧 [Admin] Re-create the channel structure")
@app_commands.default_permissions(administrator=True)
async def cmd_setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin only!", ephemeral=True)
        return
    await interaction.response.send_message("🔄 Setting up channels...", ephemeral=True)
    await channel_manager.setup_guild(interaction.guild, StoreTicketView)
    await interaction.followup.send("✅ Channels created/updated!", ephemeral=True)

# --- New Features: Kill Streaks, Weapon Mastery, Trading, Raid Alerts, Seasonal Events ---

@bot.tree.command(name="streak", description="🔥 Check your current kill streak and best streak")
@app_commands.describe(player="Optional: check another player's streak")
async def cmd_streak(interaction: discord.Interaction, player: str = None):
    if player is None:
        data = stats_engine.load_data()
        user_data = data["players"].get(str(interaction.user.id))
        if not user_data or not user_data.get("linked_name"):
            await interaction.response.send_message("Link your account with `/link <name>` first!", ephemeral=True)
            return
        player = user_data["linked_name"]
    streak = stats_engine.get_streak(player)
    embed = discord.Embed(title=f"🔥 Kill Streak — {player}", color=discord.Color.red())
    embed.add_field(name="Current Streak", value=f"{streak['current']} 🔥", inline=True)
    embed.add_field(name="Best Streak", value=f"{streak['best']} 💀", inline=True)
    if streak["best"] >= 10:
        embed.add_field(name="Status", value="🔥 RAMPAGE", inline=False)
    elif streak["best"] >= 5:
        embed.add_field(name="Status", value="⚡ Unstoppable", inline=False)
    embed.set_footer(text="DeadsideBot • Streak Tracker")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="mastery", description="🔫 Show weapon mastery levels for a player")
@app_commands.describe(player="Optional: another player's weapon mastery")
async def cmd_mastery(interaction: discord.Interaction, player: str = None):
    if player is None:
        data = stats_engine.load_data()
        user_data = data["players"].get(str(interaction.user.id))
        if not user_data or not user_data.get("linked_name"):
            await interaction.response.send_message("Link your account with `/link <name>` first!", ephemeral=True)
            return
        player = user_data["linked_name"]
    mastery = stats_engine.get_weapon_mastery(player)
    if not mastery:
        await interaction.response.send_message(f"No weapon data for '{player}'. Get some kills first!", ephemeral=True)
        return
    embed = discord.Embed(title=f"🔫 Weapon Mastery — {player}", color=discord.Color.orange())
    for weapon, info in sorted(mastery.items(), key=lambda x: x[1]["kills"], reverse=True)[:10]:
        embed.add_field(name=f"{info['tier']} {weapon}", value=f"{info['kills']} kills (Level {info['level']})", inline=False)
    embed.set_footer(text="DeadsideBot • Weapon Mastery")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="trade", description="🤝 Trade coins to another Discord user")
@app_commands.describe(user="User to send coins to", amount="How many coins to send")
async def cmd_trade(interaction: discord.Interaction, user: discord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Cannot trade 0 or negative coins!", ephemeral=True)
        return
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ Can't trade to yourself!", ephemeral=True)
        return
    success, msg = stats_engine.trade_coins(interaction.user.id, user.id, amount)
    if success:
        embed = discord.Embed(title="🤝 Trade Complete", description=f"Sent **{amount}💰** to {user.mention}\n{msg}", color=discord.Color.green())
    else:
        embed = discord.Embed(title="❌ Trade Failed", description=msg, color=discord.Color.red())
    embed.set_footer(text="DeadsideBot • Trading")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="raidalerts", description="⚡ Show recent raid/rampage alerts")
async def cmd_raidalerts(interaction: discord.Interaction):
    alerts = stats_engine.get_raid_alerts(5)
    if not alerts:
        await interaction.response.send_message("No recent raid alerts! 🔥", ephemeral=True)
        return
    embed = discord.Embed(title="⚡ Recent Raid Alerts", color=discord.Color.dark_red())
    for alert in alerts:
        emoji = "🔥" if "5" in str(alert.get("kills", 0)) else "⚡"
        embed.add_field(
            name=f"{emoji} {alert['player']}",
            value=f"{alert['kills']} kills in 30s\n{alert['time'][:19].replace('T', ' ')}",
            inline=False
        )
    embed.set_footer(text="DeadsideBot • Raid Detection")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="event", description="🎉 Show current seasonal event or trigger a new one (admin)")
async def cmd_event(interaction: discord.Interaction):
    event = stats_engine.get_seasonal_event()
    if event:
        embed = discord.Embed(
            title=f"🎉 {event['name']}",
            description=f"**Multiplier:** {event['multiplier']}x\n**Type:** {event['type']}\n**Active until:** {event.get('end', 'TBD')[:19].replace('T', ' ')}",
            color=discord.Color.gold()
        )
        embed.set_footer(text="DeadsideBot • Seasonal Events")
        await interaction.response.send_message(embed=embed)
    else:
        if interaction.user.guild_permissions.administrator:
            event = stats_engine.trigger_seasonal_event()
            embed = discord.Embed(
                title=f"🎉 {event['name']} STARTED!",
                description=f"**Multiplier:** {event['multiplier']}x\n**Type:** {event['type']}\n\nEnjoy the boosted rewards! 🔥",
                color=discord.Color.gold()
            )
            embed.set_footer(text="DeadsideBot • Seasonal Events")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No active seasonal event. Ask an admin to start one! 🎉", ephemeral=True)

# ============================================================
# MAIN
# ============================================================
def run():
    token_path = config.get("bot_token_path", "/opt/deadsidebot/token.txt")
    if not os.path.exists(token_path):
        print(f"❌ Bot token not found at {token_path}")
        print("   Run install.sh or create the token file manually.")
        sys.exit(1)

    with open(token_path) as f:
        token = f.read().strip()

    if not token:
        print("❌ Bot token is empty!")
        sys.exit(1)

    stats_engine.log("Starting DeadsideBot...")
    try:
        bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        stats_engine.log("PRIVILEGED INTENTS NOT ENABLED! Go to discord.com/developers/applications -> Bot -> Privileged Gateway Intents", "ERROR")
    except Exception as e:
        stats_engine.log(f"Bot error: {e}", "ERROR")

if __name__ == "__main__":
    run()
