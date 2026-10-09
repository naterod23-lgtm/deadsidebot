# DeadsideBot — Privacy Policy

**Last Updated:** October 9, 2026

## 1. Overview

This Privacy Policy describes how Yesukai Studios ("we", "us", "our") collects, uses, stores, and protects your data when you use DeadsideBot ("the Bot"), our Discord bot for Deadside game server communities.

We are committed to protecting your privacy and being transparent about what data we collect and why. This policy complies with the General Data Protection Regulation (GDPR), the California Consumer Privacy Act (CCPA), and other applicable privacy laws.

## 2. Data Controller

**Yesukai Studios** is the data controller responsible for your data. For privacy inquiries, contact us at **NATEROD23@gmail.com**.

## 3. What Data We Collect

### 3.1 Discord Account Data
| Data Point | Purpose | Required |
|---|---|---|
| Discord User ID | Identify users, track balances, link accounts | ✅ Yes |
| Discord Username | Display in stats, leaderboards, tickets | ✅ Yes |
| Discord Server (Guild) ID | Channel setup, multi-server support | ✅ Yes (for server owners) |
| Channel IDs | Reference channels for auto-updating content | ✅ Yes (for server owners) |
| Discord Avatar URL | Display in some embeds | ❌ No — we don't collect this |

### 3.2 Game Data (from Deadside Server via SFTP)
| Data Point | Source | Purpose |
|---|---|---|
| Killer player name | Kill log | Stats, leaderboards, killfeed |
| Victim player name | Kill log | Stats, death tracking |
| Weapon used | Kill log | Weapon mastery, stats |
| Kill distance | Kill log | Longest kill tracking |
| Kill timestamp | Kill log | Chronological killfeed |
| Player Steam ID / EOS ID | Kill log | Currently not parsed (future feature) |

### 3.3 Economy Data
| Data Point | Purpose |
|---|---|
| Coin balance | Track user's earned currency |
| Transaction history | Track store purchases, trades, gambling |
| Daily bonus claims | Prevent duplicate daily claims |
| Linked in-game name | Connect Discord account to Deadside character |
| Store tickets | Track item purchase requests and fulfillment |

### 3.4 SFTP Credentials (Server Owners Only)
| Data Point | Purpose |
|---|---|
| SFTP host IP | Connect to Deadside server |
| SFTP username | Authenticate SFTP connection |
| SFTP password | Authenticate SFTP connection |
| SFTP base path | Locate kill log file |

SFTP credentials are stored in a configuration file on our server. They are:
- Stored in plain text in a local config file (not encrypted at rest)
- Used solely to read kill logs via SFTP
- Never shared with third parties
- Never used to write, modify, or delete files on your game server
- Accessible only by server administrators with root access

**We strongly recommend using a dedicated SFTP account with read-only access where possible.**

## 4. How We Use Your Data

### 4.1 Primary Uses
1. **Display kill data** in Discord channels (killfeed, stats, leaderboards)
2. **Manage the economy** — track coin balances, process store purchases
3. **Compute statistics** — K/D ratios, weapon mastery, kill streaks, achievements
4. **Auto-create and manage channels** in your Discord server
5. **Verify Premium subscriptions** and gate premium features

### 4.2 We Do NOT Use Your Data For
- ❌ Advertising or marketing
- ❌ Selling or sharing with third parties
- ❌ Training machine learning models
- ❌ Profiling or behavioral analysis
- ❌ Credit checks or identity verification
- ❌ Any purpose unrelated to the Bot's functionality

## 5. Legal Basis for Processing (GDPR)

Under the GDPR, we process your data based on:

| Basis | Data | Justification |
|---|---|---|
| **Consent** | Discord user data, linked in-game name | You voluntarily use the Bot and `/link` your account |
| **Contract** | Premium subscription data | You pay for Premium, we provide the service |
| **Legitimate Interest** | Kill data from game server | The Bot's core purpose is to display game stats |
| **Legal Obligation** | Payment records (Premium) | Tax and financial record requirements |

You may withdraw consent at any time by unlinking your account or removing the Bot from your server.

## 6. Data Storage

### 6.1 Where Data Is Stored
- All data is stored on our server (VPS hosted in the United States).
- Data is stored in JSON files on the local filesystem.
- No cloud database, no third-party data storage, no data warehouses.
- No CDN or external content delivery.

### 6.2 Data Security
- The server is protected by SSH key authentication and firewall.
- SFTP credentials are stored in a local config file (not encrypted).
- Discord bot tokens are stored in a file with restricted permissions (chmod 600).
- No data is transmitted to third parties.
- Access to the server is limited to authorized administrators.

### 6.3 Data Retention
| Data Type | Retention Period |
|---|---|
| Player stats (kills, deaths, K/D) | Retained while Bot is in your server; deleted within 30 days of removal |
| Kill log data (recent kills) | Up to 90 days |
| Economy data (balances, transactions) | Retained while Bot is in your server; deleted within 30 days |
| Store tickets | Retained for 12 months for dispute resolution |
| Premium payment records | Retained for 7 years (legal/tax requirement) |
| Discord server data (channel IDs) | Deleted immediately when Bot is removed |
| SFTP credentials | Deleted immediately when Bot is removed or server is reconfigured |

## 7. Your Rights

### 7.1 GDPR Rights (EU/UK Users)
You have the right to:

1. **Access** — Request a copy of all data we hold about you.
2. **Rectification** — Request correction of inaccurate data.
3. **Erasure** — Request deletion of your data ("right to be forgotten").
4. **Restriction** — Request that we limit processing of your data.
5. **Portability** — Receive your data in a machine-readable format.
6. **Objection** — Object to processing based on legitimate interests.
7. **Withdraw Consent** — Withdraw consent at any time without affecting prior processing.

### 7.2 CCPA Rights (California Residents)
You have the right to:

1. **Know** — What personal information we collect and how it's used.
2. **Delete** — Request deletion of your personal information.
3. **Opt-Out** — Opt out of the sale of personal information (we do not sell data).
4. **Non-Discrimination** — Equal service regardless of exercising privacy rights.

### 7.3 How to Exercise Your Rights
Contact us at **NATEROD23@gmail.com** with:
- Your Discord user ID
- Your linked in-game name (if applicable)
- The specific right you wish to exercise

We will respond within 30 days. For erasure requests, your data will be deleted within 30 days of verification.

### 7.4 Automated Deletion
You can trigger immediate deletion of your linked data by:
1. Using `/link` with a blank or different name (unlinks your Discord from your game name)
2. Leaving a Discord server that uses the Bot
3. Requesting server owner to remove the Bot (deletes all server data)

## 8. Children's Privacy

The Bot is not directed at children under 13. We do not knowingly collect data from children under 13. If you believe a child under 13 has provided data through the Bot, contact us and we will delete it immediately.

Discord requires users to be at least 13 years old. Server owners are responsible for ensuring their community complies with Discord's age requirements.

## 9. Third-Party Services

### 9.1 Discord
The Bot operates within Discord's platform. Discord's [Privacy Policy](https://discord.com/privacy) and [Terms of Service](https://discord.com/terms) apply to all Discord interactions. We process Discord data (user IDs, usernames, server IDs) but do not control Discord's data practices.

### 9.2 Deadside / GG Host
The Bot reads kill log data from your Deadside game server hosted on GG Host via SFTP. We do not have a relationship with BadPixel Studio (Deadside developer) or GG Host. Your game server data is subject to their respective privacy policies and terms of service.

### 9.3 Payment Processors (Premium Only)
If you purchase Premium, your payment is processed by our payment processor (Stripe, PayPal, or Discord's native monetization). We receive only the payment confirmation and subscription status — we do not see or store your full credit card number, bank account, or other payment details. The payment processor's privacy policy applies to all payment data.

## 10. Data Breach Response

In the event of a data breach:

1. We will assess the scope and severity within 24 hours of discovery.
2. Affected users will be notified within 72 hours (per GDPR requirements).
3. SFTP credentials will be immediately rotated.
4. A public incident report will be published if the breach affects more than 100 users.
5. Relevant authorities will be notified as required by law.

## 11. International Data Transfers

Your data is stored on a server in the United States. If you are in the EU, UK, or other jurisdiction with data transfer restrictions, your data is transferred to the US under Standard Contractual Clauses (SCCs) or an equivalent mechanism. By using the Bot, you consent to this transfer.

## 12. Cookie Policy

The Bot does not use cookies, web beacons, or similar tracking technologies. It operates entirely through Discord's API and SFTP connections.

## 13. Changes to This Policy

We may update this Privacy Policy at any time. Material changes will be:
- Posted in our Discord support server
- Updated on this page with a new "Last Updated" date
- Communicated via email if you've provided one

Continued use of the Bot after changes constitutes acceptance of the updated policy.

## 14. Contact

For any privacy questions, concerns, or requests:

- **Email:** NATEROD23@gmail.com
- **Discord:** Join our support server (link in the Bot's `/serverinfo` command)

We aim to respond to all privacy inquiries within 30 days.

---

© 2026 Yesukai Studios. All rights reserved. DeadsideBot is not affiliated with BadPixel Studio or the Deadside game.
