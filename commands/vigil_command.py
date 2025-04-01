"""
Vigil Interactive Command Module
Provides an interactive interface for OSINT investigations
"""

import discord
from discord.ext import commands
import asyncio
import logging

logger = logging.getLogger("vigil_bot")

def create_vigil_embed():
    """Create the main Vigil command embed"""
    embed = discord.Embed(
        title="🕵️ Vigil OSINT Investigation Toolkit",
        description=(
            "Welcome to Vigil, your comprehensive OSINT investigation platform. "
            "Choose an investigation method below:"
        ),
        color=discord.Color.blue()
    )
    return embed

def create_vigil_buttons():
    """Create interactive buttons for Vigil command"""
    components = discord.ui.View()
    
    # Username Investigation Button
    username_btn = discord.ui.Button(
        style=discord.ButtonStyle.primary, 
        label="🔍 Username Search", 
        custom_id="vigil_username"
    )
    
    # Email Investigation Button
    email_btn = discord.ui.Button(
        style=discord.ButtonStyle.secondary, 
        label="📧 Email Investigation", 
        custom_id="vigil_email"
    )
    
    # Phone Number Investigation Button
    phone_btn = discord.ui.Button(
        style=discord.ButtonStyle.green, 
        label="📱 Phone Number Search", 
        custom_id="vigil_phone"
    )
    
    # IP Address Investigation Button
    ip_btn = discord.ui.Button(
        style=discord.ButtonStyle.red, 
        label="🌐 IP Address Lookup", 
        custom_id="vigil_ip"
    )
    
    async def username_callback(interaction: discord.Interaction):
        """Handler for username search button"""
        embed = discord.Embed(
            title="🔍 Username Investigation",
            description=(
                "Select a username investigation tool:\n\n"
                "• Maigret: Comprehensive cross-platform search\n"
                "• Sherlock: Social media username lookup\n"
                "• WhatsMyName: Verify username across platforms"
            ),
            color=discord.Color.blue()
        )
        
        username_tools = discord.ui.View()
        
        maigret_btn = discord.ui.Button(
            style=discord.ButtonStyle.primary, 
            label="Maigret", 
            custom_id="username_maigret"
        )
        
        sherlock_btn = discord.ui.Button(
            style=discord.ButtonStyle.secondary, 
            label="Sherlock", 
            custom_id="username_sherlock"
        )
        
        wmn_btn = discord.ui.Button(
            style=discord.ButtonStyle.green, 
            label="WhatsMyName", 
            custom_id="username_wmn"
        )
        
        async def maigret_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(UsernameModal())
        
        async def sherlock_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(UsernameModal("sherlock"))
        
        async def wmn_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(UsernameModal("wmn"))
        
        maigret_btn.callback = maigret_callback
        sherlock_btn.callback = sherlock_callback
        wmn_btn.callback = wmn_callback
        
        username_tools.add_item(maigret_btn)
        username_tools.add_item(sherlock_btn)
        username_tools.add_item(wmn_btn)
        
        await interaction.response.edit_message(embed=embed, view=username_tools)
    
    username_btn.callback = username_callback
    
    async def email_callback(interaction: discord.Interaction):
        """Handler for email investigation button"""
        await interaction.response.send_modal(EmailModal())
    
    email_btn.callback = email_callback
    
    async def phone_callback(interaction: discord.Interaction):
        """Handler for phone number investigation button"""
        await interaction.response.send_modal(PhoneModal())
    
    phone_btn.callback = phone_callback
    
    async def ip_callback(interaction: discord.Interaction):
        """Handler for IP address investigation button"""
        await interaction.response.send_modal(IPModal())
    
    ip_btn.callback = ip_callback
    
    components.add_item(username_btn)
    components.add_item(email_btn)
    components.add_item(phone_btn)
    components.add_item(ip_btn)
    
    return components

class UsernameModal(discord.ui.Modal):
    """Modal for username input"""
    def __init__(self, tool_type="maigret"):
        super().__init__(title=f"{'Maigret' if tool_type == 'maigret' else 'Sherlock' if tool_type == 'sherlock' else 'WhatsMyName'} Username Search")
        self.tool_type = tool_type
        
        self.username = discord.ui.TextInput(
            label="Username",
            placeholder="Enter the username to investigate",
            required=True,
            max_length=50
        )
        self.add_item(self.username)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process username submission"""
        username = self.username.value
        
        if self.tool_type == "maigret":
            await interaction.response.send_message(f"Searching for username {username} using Maigret...")
            # You would call the maigret search function here
        elif self.tool_type == "sherlock":
            await interaction.response.send_message(f"Searching for username {username} using Sherlock...")
            # You would call the sherlock search function here
        else:  # WhatsMyName
            await interaction.response.send_message(f"Searching for username {username} using WhatsMyName...")
            # You would call the WhatsMyName search function here

class EmailModal(discord.ui.Modal):
    """Modal for email investigation"""
    def __init__(self):
        super().__init__(title="Email Investigation")
        
        self.email = discord.ui.TextInput(
            label="Email Address",
            placeholder="Enter the email to investigate",
            required=True,
            max_length=100
        )
        self.add_item(self.email)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process email submission"""
        email = self.email.value
        await interaction.response.send_message(f"Investigating email: {email}")
        # Implement email investigation logic here

class PhoneModal(discord.ui.Modal):
    """Modal for phone number investigation"""
    def __init__(self):
        super().__init__(title="Phone Number Investigation")
        
        self.phone = discord.ui.TextInput(
            label="Phone Number",
            placeholder="Enter the phone number to investigate (E.164 format)",
            required=True,
            max_length=20
        )
        self.add_item(self.phone)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process phone number submission"""
        phone = self.phone.value
        await interaction.response.send_message(f"Investigating phone number: {phone}")
        # Implement phone number investigation logic here

class IPModal(discord.ui.Modal):
    """Modal for IP address investigation"""
    def __init__(self):
        super().__init__(title="IP Address Lookup")
        
        self.ip = discord.ui.TextInput(
            label="IP Address",
            placeholder="Enter the IP address to investigate",
            required=True,
            max_length=45
        )
        self.add_item(self.ip)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process IP address submission"""
        ip = self.ip.value
        await interaction.response.send_message(f"Investigating IP address: {ip}")
        # Implement IP address investigation logic here

def register_vigil_commands(bot):
    @bot.command(name="vigil", help="Interactive OSINT investigation toolkit")
    async def vigil(ctx):
        """
        Launch the interactive Vigil OSINT investigation toolkit
        """
        embed = create_vigil_embed()
        components = create_vigil_buttons()
        
        # Send the message with the embed and buttons
        await ctx.send(embed=embed, view=components)
