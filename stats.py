#!/usr/bin/env python3
"""
DeadsideBot Stats Engine
- SFTP log parser for Deadside kill logs
- Player stats tracking (kills, deaths, K/D, weapons, longest kill)
- Kill feed management
- Multi-server support (premium)
"""

import json
import os
import re
import hashlib
from datetime import datetime
from collections import defaultdict

try:
    import paramiko
except ImportError:
    paramiko = None

# Kill log patterns — Deadside.log uses various formats
KILL_PATTERNS = [
    # "KillerName" killed "VictimName" with "Weapon" at "Distance"m
    r'(?P<killer>[^\s]+)\s+killed\s+(?P<victim>[^\s]+)\s+with\s+(?P<weapon>[^\s]+)\s+at\s+(?P<distance>[\d.]+)',
    # Kill: killer=Name victim=Name weapon=Weapon distance=123
    r'[Kk]ill.*killer=(?P<killer>\S+)\s+victim=(?P<victim>\S+)\s+weapon=(?P<weapon>\S+).*distance=(?P<distance>[\d.]+)',
    # LogSFPS kill format
    r'LogSFPS:.*[Kk]ill.*(?P<killer>\w+).*->.*(?P<victim>\w+).*\((?P<weapon>[^,]+).*?(?P<distance>[\d.]+)',
]

# Achievement definitions
ACHIEVEMENTS = {
    "first_blood": {"name": "🩸 First Blood", "desc": "Get your first kill", "check": lambda s: s["kills"] >= 1},
    "killer": {"name": "💀 Killer", "desc": "Reach 10 kills", "check": lambda s: s["kills"] >= 10},
    "serial_killer": {"name": "🔪 Serial Killer", "desc": "Reach 50 kills", "check": lambda s: s["kills"] >= 50},
    "legend": {"name": "🏆 Legend", "desc": "Reach 100 kills", "check": lambda s: s["kills"] >= 100},
    "marksman": {"name": "🎯 Marksman", "desc": "Get a 200m+ kill", "check": lambda s: s["longest_kill"] >= 200},
    "sniper": {"name": "🎯 Sniper", "desc": "Get a 400m+ kill", "check": lambda s: s["longest_kill"] >= 400},
    "god_sniper": {"name": "🌟 God Sniper", "desc": "Get a 500m+ kill", "check": lambda s: s["longest_kill"] >= 500},
    "survivor": {"name": "🛡️ Survivor", "desc": "Die 10 times (and keep going)", "check": lambda s: s["deaths"] >= 10},
    "unstoppable": {"name": "⚡ Unstoppable", "desc": "5 kills without dying", "check": lambda s: s.get("best_streak", 0) >= 5},
    "rampage": {"name": "🔥 Rampage", "desc": "10 kill streak", "check": lambda s: s.get("best_streak", 0) >= 10},
    "weapon_master": {"name": "🔫 Weapon Master", "desc": "Kills with 5+ weapons", "check": lambda s: len(s.get("weapons", {})) >= 5},
}

# Weapon mastery tiers
WEAPON_MASTERY_TIERS = {
    10: {"name": "🎯 Novice", "level": 1},
    25: {"name": "🔫 Skilled", "level": 2},
    50: {"name": "💀 Expert", "level": 3},
    100: {"name": "🏆 Master", "level": 4},
    250: {"name": "👑 Legendary", "level": 5},
}

# Seasonal events
SEASONAL_EVENTS = [
    {"name": "🔥 Double Kill Weekend", "multiplier": 2.0, "type": "kills"},
    {"name": "💀 Deathmatch Week", "multiplier": 1.5, "type": "kills"},
    {"name": "🎯 Sniper Sunday", "multiplier": 3.0, "type": "longest_kill"},
    {"name": "🧨 Crime Spree", "multiplier": 2.0, "type": "crime"},
    {"name": "🎰 Lucky Streak", "multiplier": 1.5, "type": "gamble"},
]

class StatsEngine:
    def __init__(self, config):
        self.config = config
        self.data_path = config.get("data_path", "/opt/deadsidebot/data/deadside_data.json")
        self.log_dir = config.get("log_dir", "/opt/deadsidebot/logs")
        self.sftp_host = config.get("sftp_host", "localhost")
        self.sftp_port = config.get("sftp_port", 8822)
        self.sftp_user = config.get("sftp_user", "user")
        self.sftp_pass = config.get("sftp_pass", "pass")
        self.sftp_log_path = config.get("sftp_log_path", "/server/Logs/Deadside.log")

    def load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path) as f:
                return json.load(f)
        return {
            "players": {},
            "stats": {},
            "tickets": [],
            "last_log_position": 0,
            "longest_kill_today": {"distance": 0, "player": None, "weapon": None, "date": None},
            "processed_kill_ids": [],
            "recent_kills": [],
            "channels_setup": {},
            "achievements": {},
        }

    def save_data(self, data):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

    def log(self, msg, level="INFO"):
        os.makedirs(self.log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line, flush=True)
        with open(os.path.join(self.log_dir, "deadsidebot.log"), "a") as f:
            f.write(line + "\n")

    def fetch_new_log_lines(self):
        """Fetch new lines from Deadside.log via SFTP."""
        data = self.load_data()
        last_pos = data.get("last_log_position", 0)

        if not paramiko:
            self.log("paramiko not installed!", "ERROR")
            return []

        try:
            transport = paramiko.Transport((self.sftp_host, self.sftp_port))
            transport.connect(username=self.sftp_user, password=self.sftp_pass)
            sftp = paramiko.SFTPClient.from_transport(transport)

            try:
                file_stat = sftp.stat(self.sftp_log_path)
                file_size = file_stat.st_size
            except:
                sftp.close()
                transport.close()
                return []

            if file_size < last_pos:
                last_pos = 0

            with sftp.file(self.sftp_log_path, 'r') as f:
                f.seek(last_pos)
                new_content = f.read(file_size - last_pos).decode('utf-8', errors='replace')

            data["last_log_position"] = file_size
            self.save_data(data)

            sftp.close()
            transport.close()

            return [l for l in new_content.split('\n') if l.strip()]

        except Exception as e:
            self.log(f"SFTP error: {e}", "ERROR")
            return []

    def parse_kill(self, line):
        """Parse a kill event from a log line."""
        for pattern in KILL_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                d = match.groupdict()
                return {
                    "killer_name": d.get("killer", "").strip('"').strip("'"),
                    "victim_name": d.get("victim", "").strip('"').strip("'"),
                    "weapon": d.get("weapon", "").strip('"').strip("'"),
                    "distance": float(d.get("distance", 0)),
                    "timestamp": datetime.now().isoformat(),
                    "raw": line.strip(),
                }
        return None

    def process_new_kills(self):
        """Fetch and process new kill log entries."""
        lines = self.fetch_new_log_lines()
        if not lines:
            return []

        data = self.load_data()
        new_kills = []
        config = self.config

        for line in lines:
            kill = self.parse_kill(line)
            if not kill:
                continue

            kill_hash = hashlib.md5(line.encode()).hexdigest()
            if kill_hash in data.get("processed_kill_ids", []):
                continue
            data["processed_kill_ids"].append(kill_hash)
            if len(data["processed_kill_ids"]) > 10000:
                data["processed_kill_ids"] = data["processed_kill_ids"][-5000:]

            killer = kill["killer_name"]
            victim = kill["victim_name"]
            weapon = kill["weapon"]
            distance = kill["distance"]

            # Initialize player stats
            if killer not in data["stats"]:
                data["stats"][killer] = {"kills": 0, "deaths": 0, "weapons": {}, "longest_kill": 0, "longest_kill_weapon": None, "best_streak": 0}
            if victim not in data["stats"]:
                data["stats"][victim] = {"kills": 0, "deaths": 0, "weapons": {}, "longest_kill": 0, "longest_kill_weapon": None, "best_streak": 0}

            # Update stats
            data["stats"][killer]["kills"] += 1
            data["stats"][killer]["weapons"][weapon] = data["stats"][killer]["weapons"].get(weapon, 0) + 1
            data["stats"][victim]["deaths"] += 1

            # Update kill streak
            streaks = data.setdefault("kill_streaks", {})
            if killer not in streaks:
                streaks[killer] = {"current": 0, "best": 0}
            streaks[killer]["current"] += 1
            if streaks[killer]["current"] > streaks[killer]["best"]:
                streaks[killer]["best"] = streaks[killer]["current"]
            data["stats"][killer]["best_streak"] = streaks[killer]["best"]
            if victim not in streaks:
                streaks[victim] = {"current": 0, "best": 0}
            streaks[victim]["current"] = 0

            # Raid detection (3+ kills in 30s)
            now = datetime.now()
            killer_kills_recent = [k for k in data.get("recent_kills", [])[:10]
                                    if k["killer_name"] == killer
                                    and (now - datetime.fromisoformat(k["timestamp"])).total_seconds() < 30]
            if len(killer_kills_recent) >= 3:
                raid_type = "🔥 RAMPAGE" if len(killer_kills_recent) >= 5 else "⚡ TRIPLE KILL"
                data.setdefault("raid_alerts", []).insert(0, {
                    "player": killer, "kills": len(killer_kills_recent),
                    "time": now.isoformat(), "type": raid_type.lower().replace(" ", "_"),
                })
                if len(data["raid_alerts"]) > 20:
                    data["raid_alerts"] = data["raid_alerts"][:20]
                self.log(f"{raid_type}: {killer} got {len(killer_kills_recent)} kills in 30s!")

            if distance > data["stats"][killer]["longest_kill"]:
                data["stats"][killer]["longest_kill"] = distance
                data["stats"][killer]["longest_kill_weapon"] = weapon

            # Longest kill of the day
            today = datetime.now().strftime("%Y-%m-%d")
            if data.get("longest_kill_today", {}).get("date") != today:
                data["longest_kill_today"] = {"distance": 0, "player": None, "weapon": None, "date": today}

            if distance > data["longest_kill_today"]["distance"]:
                data["longest_kill_today"] = {"distance": distance, "player": killer, "weapon": weapon, "date": today}
                killer_discord = self._find_discord_by_name(data, killer)
                if killer_discord:
                    data["players"][killer_discord]["balance"] += config.get("longest_kill_bonus", 50)

            # Award currency to linked Discord users
            killer_discord = self._find_discord_by_name(data, killer)
            if killer_discord:
                data["players"][killer_discord]["balance"] += config.get("currency_per_kill", 10)

            victim_discord = self._find_discord_by_name(data, victim)
            if victim_discord:
                data["players"][victim_discord]["balance"] += config.get("currency_per_death", 5)

            # Store in recent kills
            kill["id"] = kill_hash[:12]
            data.setdefault("recent_kills", []).insert(0, kill)
            if len(data["recent_kills"]) > 50:
                data["recent_kills"] = data["recent_kills"][:50]

            new_kills.append(kill)
            self.log(f"Kill: {killer} killed {victim} with {weapon} at {distance}m")

            # Check achievements (premium)
            self._check_achievements(data, killer)

        self.save_data(data)
        return new_kills

    def _find_discord_by_name(self, data, game_name):
        for did, pdata in data["players"].items():
            if pdata.get("linked_name", "").lower() == game_name.lower():
                return did
        return None

    def _check_achievements(self, data, player_name):
        """Check and award achievements for a player."""
        if player_name not in data["stats"]:
            return

        stats = data["stats"][player_name]
        if "achievements" not in data:
            data["achievements"] = {}
        if player_name not in data["achievements"]:
            data["achievements"][player_name] = []

        for ach_id, ach in ACHIEVEMENTS.items():
            if ach_id not in data["achievements"][player_name] and ach["check"](stats):
                data["achievements"][player_name].append(ach_id)
                self.log(f"Achievement unlocked: {player_name} - {ach['name']}")

    def get_player_stats(self, player_name):
        data = self.load_data()
        return data["stats"].get(player_name)

    def get_leaderboard(self, limit=10):
        data = self.load_data()
        stats = data.get("stats", {})
        return sorted(stats.items(), key=lambda x: x[1]["kills"], reverse=True)[:limit]

    def get_server_stats(self):
        data = self.load_data()
        stats = data.get("stats", {})
        if not stats:
            return None

        total_kills = sum(s["kills"] for s in stats.values())
        total_deaths = sum(s["deaths"] for s in stats.values())
        all_weapons = defaultdict(int)
        for s in stats.values():
            for w, c in s["weapons"].items():
                all_weapons[w] += c

        top_weapon = max(all_weapons.items(), key=lambda x: x[1]) if all_weapons else ("None", 0)
        longest = max((s["longest_kill"] for s in stats.values()), default=0)

        return {
            "total_kills": total_kills,
            "total_deaths": total_deaths,
            "avg_kd": total_kills / total_deaths if total_deaths > 0 else total_kills,
            "active_players": len(stats),
            "top_weapon": top_weapon,
            "longest_kill": longest,
            "all_weapons": dict(all_weapons),
        }

    def get_recent_kills(self, limit=10):
        data = self.load_data()
        return data.get("recent_kills", [])[:limit]

    def get_achievements(self, player_name):
        data = self.load_data()
        return data.get("achievements", {}).get(player_name, [])

    def get_or_create_player(self, user_id, username):
        data = self.load_data()
        if str(user_id) not in data["players"]:
            data["players"][str(user_id)] = {
                "name": username, "balance": 0, "linked_name": None,
                "linked_steam_id": None, "kills": 0, "deaths": 0,
                "daily_last": None, "bounties": [], "total_earned": 0,
                "trades": 0, "last_trade": None,
            }
        return data["players"][str(user_id)]

    def get_streak(self, player_name):
        data = self.load_data()
        return data.get("kill_streaks", {}).get(player_name, {"current": 0, "best": 0})

    def get_weapon_mastery(self, player_name):
        data = self.load_data()
        stats = data.get("stats", {}).get(player_name, {})
        weapons = stats.get("weapons", {})
        mastery = {}
        for weapon, kills in weapons.items():
            tier = {"name": "🔰 Beginner", "level": 0}
            for threshold, info in sorted(WEAPON_MASTERY_TIERS.items()):
                if kills >= threshold:
                    tier = info
            mastery[weapon] = {"kills": kills, "tier": tier["name"], "level": tier["level"]}
        return mastery

    def get_raid_alerts(self, limit=5):
        data = self.load_data()
        return data.get("raid_alerts", [])[:limit]

    def trade_coins(self, from_id, to_id, amount):
        data = self.load_data()
        if str(from_id) not in data["players"] or str(to_id) not in data["players"]:
            return False, "One or both users not found"
        from_player = data["players"][str(from_id)]
        to_player = data["players"][str(to_id)]
        if from_player["balance"] < amount:
            return False, f"Insufficient balance (have {from_player['balance']})"
        if amount <= 0:
            return False, "Cannot trade 0 or negative coins"
        from_player["balance"] -= amount
        to_player["balance"] += amount
        from_player["trades"] = from_player.get("trades", 0) + 1
        from_player["last_trade"] = datetime.now().isoformat()
        data.setdefault("trades", []).append({
            "from": str(from_id), "to": str(to_id),
            "amount": amount, "time": datetime.now().isoformat(),
        })
        self.save_data(data)
        return True, f"Traded {amount}💰 to {to_player['name']}"

    def trigger_seasonal_event(self):
        import random
        data = self.load_data()
        event = random.choice(SEASONAL_EVENTS)
        event["start"] = datetime.now().isoformat()
        event["end"] = (datetime.now().replace(hour=23, minute=59)).isoformat()
        data["seasonal_event"] = event
        self.save_data(data)
        self.log(f"Seasonal event started: {event['name']}")
        return event

    def get_seasonal_event(self):
        data = self.load_data()
        event = data.get("seasonal_event")
        if event and event.get("end") and datetime.now().isoformat() > event["end"]:
            data["seasonal_event"] = None
            self.save_data(data)
            return None
        return event
