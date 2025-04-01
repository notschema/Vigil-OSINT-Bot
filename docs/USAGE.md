# Vigil OSINT Bot - Usage Instructions

This document explains how to use the Vigil OSINT Bot with the updated directory structure.

## Getting Started

1. First, make sure your environment is set up correctly:
   - Edit the `.env` file in the project root directory
   - Add your Discord bot token: `DISCORD_TOKEN=your_discord_token_here`
   - Add any other optional API keys

2. Launch the bot using one of these methods:
   - Run `launch.bat` in the root directory
   - Run `scripts\Vigil.bat` for the control panel
   - Run `python gitbot.py` directly to start the bot without the control panel

## Directory Structure

- `/config` - Configuration files
- `/docs` - Documentation
- `/scripts` - Script utilities for running and managing the bot
- OSINT tools in their respective directories (Sherlock, Maigret, etc.)

## Available Commands

The bot provides several commands for OSINT investigations. See [COMMANDS.md](COMMANDS.md) for a complete list.

## Troubleshooting

If you encounter issues:

1. **Bot won't start**:
   - Check that your Discord token is correct in the `.env` file
   - Ensure all dependencies are installed with `scripts\install_dependencies.bat`
   - Check the logs for specific error messages

2. **Scripts are not working**:
   - Ensure you're running them from the correct directory
   - For the control panel, always start from the root directory using `launch.bat`

3. **Missing features**:
   - Some features require additional API keys to be set in the `.env` file
   - Check [ENV_SETUP.md](ENV_SETUP.md) for more information on API keys

## Security Notes

- Never share your `.env` file or commit it to version control
- Regularly rotate sensitive tokens, especially if you suspect they've been compromised
