#!/usr/bin/env python3
"""
Vigil OSINT Bot - A Discord bot that consolidates multiple OSINT tools
By: Schema (imschema)
"""

import os
import sys
import json
import logging
import asyncio
import datetime
from pathlib import Path
import argparse

# Fix for aiodns issue on Windows
if sys.platform == 'win32':
    # More robust fix for Windows event loop policy
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        # Force create a new event loop with the policy
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception as e:
        print(f"Error setting event loop policy: {e}")

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Import command modules
from commands.basic_commands import register_basic_commands
from commands.github_commands import register_github_commands
from commands.username_commands import register_username_commands
from commands.email_commands import register_email_commands
from commands.breach_commands import register_breach_commands
from commands.other_commands import register_other_commands
from commands.vigil_command import register_vigil_commands
from commands.steam_commands import register_steam_commands

def setup_logging(verbose=False, quiet=False):
    """
    Configure logging based on verbosity levels
    
    Args:
        verbose (bool): Enable detailed logging
        quiet (bool): Suppress most log messages
    """
    # Determine log level
    if quiet:
        log_level = logging.ERROR
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        handlers=[
            logging.FileHandler("vigil_bot.log"),
            logging.StreamHandler()
        ]
    )

    # Set log levels for specific loggers to reduce noise
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)

    return logging.getLogger("vigil_bot")

def parse_arguments():
    """
    Parse command-line arguments for Vigil Launcher
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Vigil OSINT Bot - A comprehensive OSINT investigation tool",
        epilog="Developed by Schema (imschema)"
    )
    
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true', 
        help='Enable verbose logging with detailed output'
    )
    
    parser.add_argument(
        '-q', '--quiet', 
        action='store_true', 
        help='Suppress most log messages, only show critical errors'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='Vigil OSINT Bot v1.0.0'
    )
    
    return parser.parse_args()

def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging based on arguments
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    # Load environment variables
    load_dotenv()
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    CHECKLEAKED_TOKEN = os.getenv("CHECKLEAKED_TOKEN")
    STEAM_API_KEY = os.getenv("STEAM_API_KEY")
    ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",") if os.getenv("ADMIN_IDS") else []

    # Check for required token
    if not DISCORD_TOKEN:
        logger.error("No Discord token found. Please set the DISCORD_TOKEN environment variable.")
        sys.exit(1)

    # Check for optional tokens
    if not GITHUB_TOKEN:
        logger.warning("No GitHub token provided. API rate limits will be restricted.")
        
    if not STEAM_API_KEY or STEAM_API_KEY.strip() == "":
        logger.warning("No Steam API key provided. Steam lookup will have limited functionality.")

    # Setup Discord intents
    intents = discord.Intents.default()
    intents.message_content = True

    # Initialize bot with command prefix
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    # Create temp directory if it doesn't exist
    TEMP_DIR = Path("temp")
    TEMP_DIR.mkdir(exist_ok=True)

    # Bot events
    @bot.event
    async def on_ready():
        """Called when the bot is ready and connected to Discord"""
        logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
        logger.info(f"Connected to {len(bot.guilds)} guilds")
        
        # Set bot status
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="OSINT investigations | !help"
        ))

    @bot.event
    async def on_command_error(ctx, error):
        """Global error handler for command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`. Use `!help {ctx.command}` for proper usage.")
            return
        
        # Log other errors
        logger.error(f"Error in {ctx.command} command: {str(error)}")
        await ctx.send(f"❌ An error occurred: {str(error)}")

    # Register all command sets
    def register_all_commands():
        register_basic_commands(bot)
        register_github_commands(bot, GITHUB_TOKEN)
        register_username_commands(bot)
        register_email_commands(bot)
        register_breach_commands(bot, CHECKLEAKED_TOKEN)
        register_other_commands(bot)
        register_vigil_commands(bot)
        register_steam_commands(bot, STEAM_API_KEY)

    try:
        register_all_commands()
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure as e:
        logger.error(f"Authentication error: {str(e)}")
    except ImportError as e:
        logger.error(f"Critical import error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
