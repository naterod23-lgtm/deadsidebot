#!/usr/bin/env bash
# DeadsideBot — One-command installer
# Usage: bash install.sh

set -e

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  💀 DeadsideBot — Discord Bot for Deadside Servers"
echo "  The all-in-one bot: killfeed, stats, economy, store, more"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo bash install.sh)"
  exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --break-system-packages discord.py paramiko 2>&1 | tail -3

# Create directories
INSTALL_DIR="/opt/deadsidebot"
mkdir -p "$INSTALL_DIR" "$INSTALL_DIR/logs" "$INSTALL_DIR/data" "$INSTALL_DIR/shared"

# Copy bot files
echo "📂 Setting up bot files..."
for f in bot.py config.py economy.py stats.py tickets.py channels.py commands.py tasks.py premium.py; do
  if [ -f "$f" ]; then cp "$f" "$INSTALL_DIR/"; fi
done

# Get credentials
echo ""
echo "🔑 Bot Configuration"
echo "───────────────────────────────────────────"

# Discord Bot Token
read -p "Enter your Discord Bot Token: " BOT_TOKEN
echo "$BOT_TOKEN" > "$INSTALL_DIR/token.txt"
chmod 600 "$INSTALL_DIR/token.txt"

# Deadside Server SFTP
echo ""
echo "🎮 Deadside Server SFTP Configuration"
echo "   (Found in your GG Host gamepanel: gamepanel.gghost.games)"
echo ""
read -p "SFTP Host IP: " SFTP_HOST
read -p "SFTP Username (short account name, not email): " SFTP_USER
read -p "SFTP Password: " SFTP_PASS
read -p "SFTP Port [8822]: " SFTP_PORT
SFTP_PORT=${SFTP_PORT:-8822}
read -p "Server base path (e.g. /169.150.231.113_26664): " SFTP_BASE

# Write config
cat > "$INSTALL_DIR/config.json" << EOF
{
  "bot_token_path": "$INSTALL_DIR/token.txt",
  "sftp_host": "$SFTP_HOST",
  "sftp_port": $SFTP_PORT,
  "sftp_user": "$SFTP_USER",
  "sftp_pass": "$SFTP_PASS",
  "sftp_base": "$SFTP_BASE",
  "sftp_log_path": "$SFTP_BASE/Logs/Deadside.log",
  "data_path": "$INSTALL_DIR/data/deadside_data.json",
  "log_dir": "$INSTALL_DIR/logs",
  "currency_per_kill": 10,
  "currency_per_death": 5,
  "longest_kill_bonus": 50,
  "daily_bonus": 20,
  "monitor_interval": 60,
  "leaderboard_interval": 600,
  "stats_interval": 900
}
EOF

# Create systemd service
echo ""
echo "⚙️  Creating systemd service..."

cat > /etc/systemd/system/deadsidebot.service << EOF
[Unit]
Description=DeadsideBot — Discord Bot for Deadside Servers
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/bot.py
Restart=always
RestartSec=30
User=root
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable deadsidebot.service
systemctl start deadsidebot.service

sleep 3
STATUS=$(systemctl is-active deadsidebot.service)

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ DeadsideBot Installation Complete!"
echo ""
echo "  Status: $STATUS"
echo "  Bot files: $INSTALL_DIR"
echo "  Config: $INSTALL_DIR/config.json"
echo "  Logs: journalctl -u deadsidebot -f"
echo ""
echo "  Next steps:"
echo "  1. Invite your bot to your Discord server with Admin perms"
echo "  2. The bot will auto-create all channels on join"
echo "  3. Use /link <your_ingame_name> to start earning coins"
echo ""
echo "  Commands: /stats /leaderboard /serverkd /balance /store"
echo "             /buy /gamble /crime /daily /killfeed /link"
echo "═══════════════════════════════════════════════════════════════"
