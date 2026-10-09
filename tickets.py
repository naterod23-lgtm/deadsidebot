#!/usr/bin/env python3
"""
DeadsideBot Ticket System
- Store ticket creation with private channels
- Admin fulfillment with Discord buttons
- Auto-refund on cancel/reject
"""

import json
import os
from datetime import datetime

import discord
from discord import ui

class StoreTicketView(ui.View):
    """The Create Ticket button shown in #store."""
    def __init__(self, stats_engine=None):
        super().__init__(timeout=None)
        self.stats_engine = stats_engine

    @ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.primary, custom_id="ds_create_ticket_btn", emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
        data = self.stats_engine.load_data() if self.stats_engine else {}
        player = self.stats_engine.get_or_create_player(interaction.user.id, interaction.user.name) if self.stats_engine else {"balance": 0, "linked_name": None}

        guild = interaction.guild
        ticket_count = len(data.get("tickets", [])) + 1

        # Find or create category
        category = discord.utils.get(guild.categories, name="🛒 STORE")
        if not category:
            category = discord.utils.get(guild.categories, name="Store Tickets")
        if not category:
            category = await guild.create_category("Store Tickets")

        channel_name = f"ticket-{ticket_count:04d}-{interaction.user.name}".lower()[:50]
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for role in guild.roles:
            if role.permissions.administrator or "admin" in role.name.lower():
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        try:
            channel = await guild.create_text_channel(
                channel_name, category=category, overwrites=overwrites,
                topic=f"Store Ticket #{ticket_count} - {interaction.user.name}"
            )
        except Exception as e:
            await interaction.response.send_message("Failed to create ticket channel!", ephemeral=True)
            return

        ticket = {
            "id": ticket_count,
            "user_id": str(interaction.user.id),
            "user_name": interaction.user.name,
            "linked_name": player.get("linked_name", "NOT LINKED"),
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "channel_id": str(channel.id),
            "items": [],
        }
        data.setdefault("tickets", []).append(ticket)
        if self.stats_engine:
            self.stats_engine.save_data(data)

        embed = discord.Embed(
            title=f"🎫 Store Ticket #{ticket_count}",
            description=(
                f"Welcome {interaction.user.mention}!\n\n"
                f"**Your IGN:** {player.get('linked_name', 'NOT LINKED — use /link <name>')}\n"
                f"**Your Balance:** {player.get('balance', 0)} 💰\n\n"
                f"To add items to your order, use `/buy <item> <qty>`.\n"
                f"When done, click **Submit Order** below.\n"
                f"An admin will fulfill it in-game.\n\n"
                f"⚠️ Make sure you're online and at a safe location in-game!"
            ),
            color=discord.Color.orange()
        )
        embed.set_footer(text="DeadsideBot • Deadside Store")

        view = TicketOrderView(ticket_count, self.stats_engine)
        await channel.send(content=f"{interaction.user.mention} | @here", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket #{ticket_count} created! Check {channel.mention}", ephemeral=True)


class TicketOrderView(ui.View):
    """Submit/Cancel buttons in a ticket channel."""
    def __init__(self, ticket_id, stats_engine=None):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.stats_engine = stats_engine

    @ui.button(label="✅ Submit Order", style=discord.ButtonStyle.success, custom_id="ds_submit_order_btn")
    async def submit_order(self, interaction: discord.Interaction, button: ui.Button):
        data = self.stats_engine.load_data() if self.stats_engine else {}
        ticket = next((t for t in data.get("tickets", []) if t["id"] == self.ticket_id), None)
        if not ticket:
            await interaction.response.send_message("Ticket not found!", ephemeral=True)
            return
        if ticket["status"] != "open":
            await interaction.response.send_message("This ticket is already submitted!", ephemeral=True)
            return

        ticket["status"] = "submitted"
        if self.stats_engine:
            self.stats_engine.save_data(data)

        items_str = "\n".join(f"• {it['qty']}x {it['name']} — {it['cost']}💰" for it in ticket.get("items", [])) or "No items added"
        total = sum(it["cost"] for it in ticket.get("items", []))

        embed = discord.Embed(
            title=f"📦 Order Submitted — Ticket #{self.ticket_id}",
            description=f"**Player:** {ticket['user_name']} ({ticket['linked_name']})\n**Total:** {total}💰\n\n**Items:**\n{items_str}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Admin Action", value="1. Join Deadside\n2. Find the player\n3. Spawn the items\n4. Click 'Fulfilled' below", inline=False)

        view = FulfillView(self.ticket_id, self.stats_engine)
        await interaction.response.send_message(embed=embed, view=view)

    @ui.button(label="❌ Cancel Ticket", style=discord.ButtonStyle.danger, custom_id="ds_cancel_ticket_btn")
    async def cancel_ticket(self, interaction: discord.Interaction, button: ui.Button):
        data = self.stats_engine.load_data() if self.stats_engine else {}
        for t in data.get("tickets", []):
            if t["id"] == self.ticket_id:
                t["status"] = "cancelled"
                total = sum(it["cost"] for it in t.get("items", []))
                if total > 0:
                    player = data["players"].get(t["user_id"], {})
                    player["balance"] += total
                if self.stats_engine:
                    self.stats_engine.save_data(data)
                await interaction.response.send_message(f"❌ Ticket #{self.ticket_id} cancelled. {total}💰 refunded.")
                return
        await interaction.response.send_message("Ticket not found!", ephemeral=True)


class FulfillView(ui.View):
    """Fulfilled/Reject buttons for admins."""
    def __init__(self, ticket_id, stats_engine=None):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.stats_engine = stats_engine

    @ui.button(label="✅ Fulfilled", style=discord.ButtonStyle.success, custom_id="ds_fulfilled_btn")
    async def fulfilled(self, interaction: discord.Interaction, button: ui.Button):
        data = self.stats_engine.load_data() if self.stats_engine else {}
        for t in data.get("tickets", []):
            if t["id"] == self.ticket_id:
                t["status"] = "fulfilled"
                if self.stats_engine:
                    self.stats_engine.save_data(data)
                await interaction.response.send_message(f"✅ Ticket #{self.ticket_id} fulfilled by {interaction.user.mention}! Player notified.")
                return
        await interaction.response.send_message("Ticket not found!", ephemeral=True)

    @ui.button(label="❌ Reject", style=discord.ButtonStyle.danger, custom_id="ds_reject_btn")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        data = self.stats_engine.load_data() if self.stats_engine else {}
        for t in data.get("tickets", []):
            if t["id"] == self.ticket_id:
                t["status"] = "rejected"
                total = sum(it["cost"] for it in t.get("items", []))
                if total > 0:
                    player = data["players"].get(t["user_id"], {})
                    player["balance"] += total
                if self.stats_engine:
                    self.stats_engine.save_data(data)
                await interaction.response.send_message(f"❌ Ticket #{self.ticket_id} rejected. {total}💰 refunded to {t['user_name']}.")
                return
        await interaction.response.send_message("Ticket not found!", ephemeral=True)
