# DeadsideBot — Sellable Discord Bot for Deadside Servers

## Overview
A premium, self-hosted Deadside Discord bot with a generous free tier and optional premium features. Designed to be user-friendly, fun, and more feature-rich than competing bots (DSKF, APB).

## Features

### Free Tier (Everything you need to run a great server)
- **Live Killfeed** — Real-time PvP kills with killer, victim, weapon, distance, timestamp
- **Player Stats** — Kills, deaths, K/D, best weapon, longest kill, weapon breakdown
- **Leaderboard** — Auto-updating top killers (every 10 min)
- **Server Stats** — Server-wide K/D, total kills/deaths, top weapon, longest kill
- **Player Linking** — Link Discord to in-game name (supports multiple aliases)
- **Economy System** — Earn coins from kills (10), deaths (5), longest kill bonus (50), daily (20)
- **Store** — 20+ items with ticket-based fulfillment system
- **Gambling** — Coinflip (2x) and dice (up to 3x)
- **Crime** — Risk/reward currency earning with fun outcomes
- **Auto Channel Setup** — Creates full channel structure on join
- **Welcome Messages** — Auto-welcome new members
- **Connection Logs** — Player join/leave alerts
- **Killfeed Channel** — Dedicated kill feed with live updates
- **13+ Slash Commands** — Full Discord slash command integration

### Premium Tier ($8.99/mo or $79/yr)
- **Bounty System** — Place bounties on players, track kills, notify results
- **Achievements** — Unlock badges for milestones (100 kills, 500m snipe, etc.)
- **Multi-Server Support** — Manage multiple Deadside servers from one bot
- **Custom Branding** — White-label embeds with your server's name/logo
- **Season Resets** — Track stats per season with automatic resets
- **Advanced Analytics** — Weekly/monthly reports, trend graphs
- **Anti-Cheat Flags** — Detect suspicious patterns (impossible distances, etc.)
- **Unlimited Store Items** — Add custom items to the store
- **Webhook Integration** — Server event alerts to external services
- **Priority Support** — Fast response to issues

## Architecture
```
deadside-bot/
├── bot.py              # Main entry point
├── config.py           # Configuration management
├── economy.py          # Economy system (store, gamble, crime)
├── stats.py            # SFTP log parser & stats tracking
├── tickets.py          # Ticket system for store fulfillment
├── channels.py         # Auto channel creation & management
├── commands.py         # All slash commands
├── tasks.py            # Background tasks (killfeed, leaderboard, etc.)
├── premium.py          # Premium feature gates
├── requirements.txt    # Python dependencies
├── install.sh          # One-command installer
└── README.md           # Documentation
```

## Setup
1. Create a Discord bot at discord.com/developers/applications
2. Enable Privileged Gateway Intents (Server Members + Message Content)
3. Run `bash install.sh` on your server
4. Enter your bot token and SFTP details when prompted
5. Invite the bot to your server with Administrator permissions
6. Done! The bot auto-creates all channels

## Why It's Better Than DSKF
- **Free tier includes** what DSKF charges for
- **Economy + Store** — no competitor has this
- **Gambling + Crime** — keeps users engaged and coming back
- **Auto-setup** — no manual channel creation needed
- **Ticket system** — built-in store with admin fulfillment
- **Fun-first design** — built for engagement, not just data
