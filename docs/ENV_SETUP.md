# Vigil OSINT Bot - Environment Setup Guide

This guide explains how to set up the environment variables needed for the Vigil OSINT Bot.

## Using the .env File

The Vigil OSINT Bot uses environment variables for storing sensitive information like API tokens. The easiest way to manage these is using the `.env` file in the project directory.

1. Locate the `.env` file in the project root directory
2. Open it with a text editor
3. Replace the placeholder values with your actual tokens and keys
4. Save the file

Example `.env` file content:
```
DISCORD_TOKEN=your_discord_token_here
GITHUB_TOKEN=your_github_token_here
CHECKLEAKED_TOKEN=your_checkleaked_token_here
```

## Required Variables

* `DISCORD_TOKEN` - Your Discord bot token (required)
  * Get this from the [Discord Developer Portal](https://discord.com/developers/applications) in the Bot section

## Optional Variables

* `GITHUB_TOKEN` - GitHub personal access token
  * Increases rate limits for GitHub API requests
  * Get this from [GitHub Settings > Developer Settings > Personal access tokens](https://github.com/settings/tokens)

* `CHECKLEAKED_TOKEN` - Token for breach data searches
  * By default uses the included token

* `ADMIN_IDS` - Comma-separated list of Discord user IDs for admin commands
  * Example: `ADMIN_IDS=123456789012345678,987654321098765432`

* `WEATHER_API_KEY` - For future weather API integration

## Alternative Setup Methods

If you prefer not to use the `.env` file, you can set environment variables directly in your system:

**Windows:**
```
set DISCORD_TOKEN=your_token_here
```

**Linux/Mac:**
```
export DISCORD_TOKEN=your_token_here
```

## Security Notes

* Never commit your `.env` file to version control
* The `.env` file is already in `.gitignore` to prevent accidental commits
* Regularly rotate sensitive tokens, especially if you suspect they've been compromised

## Troubleshooting

If the bot fails to start with a message about missing token:
1. Check that you've properly set up the `.env` file
2. Verify that the token is correct and not expired
3. Try setting the environment variable directly in the system
