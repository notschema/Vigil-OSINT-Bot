"""
Basic commands module for Vigil OSINT Bot
"""

import datetime
import discord
from discord.ext import commands

def register_basic_commands(bot):
    # First, create a command to get detailed help for a specific command
    @bot.command(name="help_command", aliases=["hc"])
    async def help_command(ctx, command_name: str = None):
        """Get detailed help for a specific command"""
        if command_name is None:
            await ctx.send("❌ Please specify a command name. Usage: `!help_command <command_name>`")
            return
            
        # Get the command object
        command = bot.get_command(command_name)
        if command is None:
            await ctx.send(f"❌ Command `{command_name}` not found.")
            return
            
        # Create embed
        embed = discord.Embed(
            title=f"Help: !{command.name}",
            description=command.help or "No detailed help available.",
            color=discord.Color.blue()
        )
        
        # Add command details
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join([f"!{alias}" for alias in command.aliases]),
                inline=False
            )
            
        # Add usage information from docstring
        if command.callback.__doc__:
            doc_lines = command.callback.__doc__.strip().split('\n')
            usage_info = ""
            for line in doc_lines:
                if "Usage:" in line or "Example:" in line:
                    usage_info += line.strip() + "\n"
            
            if usage_info:
                embed.add_field(name="Usage", value=usage_info, inline=False)
                
        # Add cooldown info if present
        for decorator in command.checks:
            if isinstance(decorator, commands.Cooldown):
                embed.add_field(
                    name="Cooldown",
                    value=f"{decorator.rate} uses every {decorator.per} seconds",
                    inline=False
                )
                
        # Send the embed
        await ctx.send(embed=embed)
        
    @bot.command(name="cooldown", aliases=["cd"])
    async def cooldown_info(ctx):
        """Show information about command cooldowns and privileged roles"""
        embed = discord.Embed(
            title="Vigil Command Cooldown System",
            description="Information about command cooldowns and how to bypass them",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="Standard Cooldowns",
            value="To prevent abuse, all commands have a standard cooldown of 30 seconds between uses for regular users.",
            inline=False
        )
        
        embed.add_field(
            name="Privileged Roles",
            value="Users with the following role have reduced cooldowns (5 seconds):\n"
                 "• **Vigil - Admin**\n\n"
                 "Regular users with the **Vigil - User** role have a standard 30-second cooldown.\n\n"
                 "These roles can be assigned by server administrators.",
            inline=False
        )
        
        embed.add_field(
            name="Admin IDs",
            value="Users listed in the ADMIN_IDS environment variable also "
                 "automatically receive reduced cooldowns regardless of their roles.",
            inline=False
        )
        
        embed.add_field(
            name="Usage Recommendation",
            value="Even with reduced cooldowns, please use commands responsibly "
                 "to ensure fair resource allocation for all users.",
            inline=False
        )
        
        embed.set_footer(text="Contact server administrators for role requests")
        
        await ctx.send(embed=embed)
    @bot.command(name="help")
    async def help(ctx, command_name=None):
        """Show help information for all commands or for a specific command"""
        embed = discord.Embed(
            title="Vigil OSINT Bot - Help",
            description="A powerful Discord bot for OSINT investigations",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.set_footer(text="Developed by Schema")
        
        if command_name:
            # Help for specific command
            command = bot.get_command(command_name)
            if command:
                embed.add_field(name=f"!{command.name}", value=command.help or "No description available", inline=False)
                embed.add_field(name="Usage", value=f"!{command.name} {command.signature}", inline=False)
                if command.aliases:
                    embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
            else:
                embed.description = f"Command `{command_name}` not found. Use `!help` to see all available commands."
        else:
            # General help - categorize commands
            categories = {
                "General": [],
                "Username Search": [],
                "Social Media": [],
                "Email": [],
                "Breach Data": [],
                "GitHub": [], 
                "Steam": [],
                "Documents": [],
                "Under Construction": [],
                "Other": []
            }
            
            for command in bot.commands:
                # Skip hidden commands
                if command.hidden:
                    continue
                    
                # Categorize commands
                if command.name in ["help", "ping", "about", "help_command", "cooldown"]:
                    categories["General"].append(command)
                elif command.name in ["sherlock", "wmn", "whatsmyname", "maigret"]:
                    categories["Username Search"].append(command)
                elif command.name in ["masto", "twitter", "insta", "socialscan"]:
                    categories["Social Media"].append(command)
                elif command.name in ["gmail", "email", "mail"]:
                    categories["Email"].append(command)
                elif command.name in ["breach", "breachx", "advbreach", "xbreach", "leakcheck", "crackhash", "hash", "breachhelp"]:
                    categories["Breach Data"].append(command)
                elif command.name in ["gituser", "gitemail", "gitrepo", "gitrepos", "gitkeys"]:
                    categories["GitHub"].append(command)
                elif command.name in ["steam", "steamlookup", "steamid"]:
                    categories["Steam"].append(command)
                elif command.name in ["gdoc", "xeuledoc"]:
                    categories["Documents"].append(command)
                elif command.name in ["weather"]:
                    categories["Under Construction"].append(command)
                else:
                    categories["Other"].append(command)
            
            # Add fields for each category (only if commands exist in that category)
            for category, cmds in categories.items():
                if cmds:
                    commands_text = "\n".join([f"`!{cmd.name}` - {cmd.help.split('.')[0] if cmd.help else 'No description'}" for cmd in cmds])
                    embed.add_field(name=category, value=commands_text, inline=False)
            
            embed.add_field(
                name="Detailed Help",
                value="Use `!help <command>` for detailed information about a specific command.\nUse `!breachhelp` for specialized help with breach-related commands.",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @bot.command(name="ping")
    async def ping(ctx):
        """Check the bot's response time"""
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Bot latency: {latency}ms")

    @bot.command(name="about")
    async def about(ctx):
        """Show information about the bot"""
        embed = discord.Embed(
            title="Vigil OSINT Bot",
            description="A powerful Discord bot that consolidates multiple OSINT tools into a single interface.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="Version", value="2.0", inline=True)
        embed.add_field(name="Developer", value="Schema", inline=True)
        embed.add_field(name="Framework", value="discord.py", inline=True)
        embed.add_field(
            name="Integrated Tools",
            value="Sherlock, Maigret, WhatsMyName, CheckLeaked, XeuleDoc, and more.",
            inline=False
        )
        embed.add_field(
            name="GitHub Repository",
            value="[Vigil OSINT Bot](https://github.com/notschema/Vigil_OSINT_Bot)",
            inline=False
        )
        
        embed.set_footer(text="For bugs/suggestions, contact: imschema")
        
        await ctx.send(embed=embed)
