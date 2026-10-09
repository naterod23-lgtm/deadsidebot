#!/usr/bin/env python3
"""
DeadsideBot Configuration
"""

import json
import os

CONFIG_PATH = os.environ.get("DEADSIDEBOT_CONFIG", "/opt/deadsidebot/config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "bot_token_path": "/opt/deadsidebot/token.txt",
        "sftp_host": "localhost",
        "sftp_port": 8822,
        "sftp_user": "user",
        "sftp_pass": "pass",
        "sftp_base": "/server",
        "sftp_log_path": "/server/Logs/Deadside.log",
        "data_path": "/opt/deadsidebot/data/deadside_data.json",
        "log_dir": "/opt/deadsidebot/logs",
        "currency_per_kill": 10,
        "currency_per_death": 5,
        "longest_kill_bonus": 50,
        "daily_bonus": 20,
        "monitor_interval": 60,
        "leaderboard_interval": 600,
        "stats_interval": 900,
        "premium_enabled": False,
        "premium_key": None,
        "server_name": "Deadside Server",
    }

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
