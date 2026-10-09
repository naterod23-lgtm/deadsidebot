#!/usr/bin/env python3
"""
DeadsideBot Background Tasks
- Log monitor (killfeed polling)
- Leaderboard auto-update
- Server stats auto-update
"""

import os
from datetime import datetime
from discord.ext import tasks

class BotTasks:
    def __init__(self, bot, stats_engine, channel_manager, config):
        self.bot = bot
        self.stats = stats_engine
        self.channels = channel_manager
        self.config = config

    async def start_all(self):
        """Start all background tasks."""
        self.log_monitor.start()
        self.leaderboard_update.start()
        self.stats_update.start()

    @tasks.loop(seconds=60)
    async def log_monitor(self):
        """Poll Deadside.log for new kills every 60s and post to #killfeed."""
        try:
            new_kills = self.stats.process_new_kills()
            if new_kills:
                self.stats.log(f"Processed {len(new_kills)} new kills")
                import discord
                for guild in self.bot.guilds:
                    ch = self.channels.get_channel(guild, "killfeed")
                    if not ch:
                        continue
                    for kill in new_kills:
                        embed = discord.Embed(
                            title="💀 Kill",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="Killer", value=kill["killer_name"], inline=True)
                        embed.add_field(name="Victim", value=kill["victim_name"], inline=True)
                        embed.add_field(name="Weapon", value=kill["weapon"], inline=True)
                        embed.add_field(name="Distance", value=f"{kill['distance']}m", inline=True)
                        embed.set_footer(text="DeadsideBot • Live Killfeed")
                        try:
                            await ch.send(embed=embed)
                        except:
                            pass
        except Exception as e:
            self.stats.log(f"Log monitor error: {e}", "ERROR")

    @tasks.loop(minutes=10)
    async def leaderboard_update(self):
        """Update #leaderboard every 10 minutes."""
        try:
            import discord
            leaderboard = self.stats.get_leaderboard(15)
            if not leaderboard:
                return
            for guild in self.bot.guilds:
                ch = self.channels.get_channel(guild, "leaderboard")
                if not ch:
                    continue
                embed = discord.Embed(
                    title="🏆 Leaderboard (Auto-updated)",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                for i, (name, s) in enumerate(leaderboard):
                    kd = s["kills"] / s["deaths"] if s["deaths"] > 0 else s["kills"]
                    medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
                    embed.add_field(
                        name=f"{medal} {name}",
                        value=f"K: {s['kills']} | D: {s['deaths']} | K/D: {kd:.2f} | Longest: {s['longest_kill']}m",
                        inline=False
                    )
                embed.set_footer(text="Auto-updated every 10 min • DeadsideBot")
                try:
                    await ch.purge(limit=5)
                    await ch.send(embed=embed)
                except:
                    pass
        except Exception as e:
            self.stats.log(f"Leaderboard update error: {e}", "ERROR")

    @tasks.loop(minutes=15)
    async def stats_update(self):
        """Update #server-stats every 15 minutes."""
        try:
            import discord
            server_stats = self.stats.get_server_stats()
            if not server_stats:
                return
            data = self.stats.load_data()
            lkd = data.get("longest_kill_today", {})
            for guild in self.bot.guilds:
                ch = self.channels.get_channel(guild, "server-stats")
                if not ch:
                    continue
                embed = discord.Embed(
                    title="📊 Server Stats (Auto-updated)",
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Total Kills", value=str(server_stats["total_kills"]), inline=True)
                embed.add_field(name="Total Deaths", value=str(server_stats["total_deaths"]), inline=True)
                embed.add_field(name="Active Players", value=str(server_stats["active_players"]), inline=True)
                embed.add_field(name="Top Weapon", value=f"{server_stats['top_weapon'][0]} ({server_stats['top_weapon'][1]} kills)", inline=False)
                if lkd.get("player"):
                    embed.add_field(name="🏆 Longest Kill Today", value=f"{lkd['player']} — {lkd['distance']}m ({lkd['weapon']})", inline=False)
                embed.set_footer(text="Auto-updated every 15 min • DeadsideBot")
                try:
                    await ch.purge(limit=5)
                    await ch.send(embed=embed)
                except:
                    pass
        except Exception as e:
            self.stats.log(f"Stats update error: {e}", "ERROR")
