# Vigil OSINT Bot 🔍

<img width="650" alt="Vigil OSINT Banner" src="https://github.com/notschema/Vigil_OSINT_Bot/assets/104733166/a0277f17-f13b-4116-be75-76899e0cf6b6">

## What is Vigil? 🧠

Vigil is a powerful Discord bot that consolidates multiple open-source intelligence (OSINT) tools into a single interface. It enables investigators, security researchers, and intelligence analysts to conduct thorough investigations directly from Discord. With over 15 integrated OSINT tools, Vigil serves as a comprehensive reconnaissance platform for modern cybersecurity operations.

Originally inspired by several OSINT bots, Vigil has evolved into a completely custom solution with extensive enhancements and unique features designed specifically for cybersecurity professionals and investigators.

## Features 🚀

### Core Capabilities
- ✅ **Username Search**: Find social media accounts across 1000+ platforms using Sherlock, Maigret, and WhatsMyName
- ✅ **Email Intelligence**: Discover accounts associated with email addresses
- ✅ **Breach Data Search**: Access and analyze data from breach databases
- ✅ **GitHub Intelligence**: Investigate GitHub users, repositories, and extract sensitive data
- ✅ **Steam Reconnaissance**: Analyze Steam profiles and gaming activities
- ✅ **Document Analysis**: Extract metadata from Google Documents
- ✅ **And More**: Continuously expanding feature set

### Technical Features
- ✅ **Docker Containerization**: Fully working with Docker for easy deployment
- ✅ **Discord Integration**: Seamless connection with Discord's API
- ✅ **API Dashboard**: Web-based control panel for monitoring and management
- ✅ **Modular Design**: Easily extendable architecture for adding new tools

## Why Use Vigil? 🦾

Traditional OSINT investigations require opening numerous tools and scripts, switching between applications, and managing multiple terminal windows. This becomes especially challenging on mobile devices.

**Vigil solves these problems by:**
- Consolidating 15+ OSINT tools into a single Discord bot interface
- Enabling on-the-go investigations directly from your phone
- Providing immediate results through an intuitive command system
- Integrating seamlessly with Discord communities and investigation teams

Whether you're a CTF competitor, cybersecurity professional, or digital investigator, Vigil streamlines your workflow by eliminating the need to juggle multiple tools simultaneously.

## Installation

### Docker Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/notschema/Vigil_OSINT_Bot.git
cd Vigil_OSINT_Bot

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your Discord token and other API keys

# Start the bot with Docker
docker-compose up -d
```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/notschema/Vigil_OSINT_Bot.git
   cd Vigil_OSINT_Bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
   # Install Maigret separately
   pip install maigret
   ```

3. Set up your environment variables:
   - Create a `.env` file based on the example
   - Add your Discord token and other API keys

4. Run the bot:
   ```bash
   python vigil.py
   ```

## Environment Configuration

The following environment variables can be configured in your `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Your Discord bot token | Yes |
| `GITHUB_TOKEN` | GitHub API token for enhanced lookups | No |
| `CHECKLEAKED_TOKEN` | Token for breach data searches | No |
| `STEAM_API_KEY` | Steam API key for detailed lookups | No |
| `ADMIN_IDS` | Comma-separated Discord IDs for admin access | No |

## Commands

Vigil provides a comprehensive set of commands for OSINT investigations:

### General Commands
- `!help` - Show all available commands
- `!help <command>` - Get detailed help for a specific command
- `!ping` - Check the bot's response time
- `!about` - Show information about the bot

### Username Search
- `!sherlock <username>` - Find accounts across 300+ platforms
- `!maigret <username>` - Advanced account discovery with detailed reporting
- `!wmn <username>` - Quick search using WhatsMyName

### Social Media
- `!masto <username>` - Search for Mastodon accounts
- `!twitter <username>` - Analyze Twitter/X profiles
- `!insta <username>` - Gather information from Instagram
- `!socialscan <username>` - Check username availability across platforms

### Email Intelligence
- `!email <email>` - Check which websites an email is registered on
- `!gmail <email>` - Specialized checks for Gmail addresses

### Breach Data
- `!breach <query> <type>` - Search for data in breaches
- `!breachx <query> <type>` - Advanced breach search with experimental API
- `!crackhash <hash>` - Attempt to decrypt password hashes
- `!leakcheck <query> <type>` - Search using LeakCheck API
- `!breachhelp` - Get detailed help with breach commands

### GitHub Intelligence
- `!gituser <username>` - Get detailed GitHub user information
- `!gitemail <email>` - Find GitHub users by email address
- `!gitrepo <username/repo>` - Analyze GitHub repositories
- `!gitrepos <username>` - List all repositories for a user
- `!gitkeys <username OR username/repo>` - Look for exposed API keys

### Steam Intelligence
- `!steam <username/URL/ID>` - Analyze Steam profiles

### Document Analysis
- `!gdoc <URL>` - Extract metadata from Google Documents

## Advanced Deployment

For more advanced deployment options, including Unraid setup, check out the `UNRAID-SETUP.md` file in this repository.

## Project Structure

```
├── api/                # FastAPI backend for bot control
├── commands/           # Bot command modules
│   ├── basic_commands.py
│   ├── breach_commands.py
│   ├── email_commands.py
│   └── ...
├── frontend/           # Next.js web interface
├── CheckLeaked/        # Breach data search module
├── Maigret/            # Username search module
├── WhatsMyName/        # Username search module
├── holehe/             # Email verification module
├── Masto/              # Mastodon search module
├── xeuledoc/           # Google Doc analysis
├── docker-compose.yml  # Standard Docker configuration
├── Dockerfile          # Main Docker build configuration
├── requirements.txt    # Python dependencies
└── vigil.py            # Main bot application
```

## License

This project is proprietary software released under a custom license. See the LICENSE file for details. Commercial use without permission is strictly prohibited.

## About the Developer

**GitHub: [notschema (Schema)](https://github.com/notschema)**  
**Discord: imschema**

---

⚠️ **Disclaimer**: This tool is for educational and legitimate security research purposes only. The developer assumes no liability for misuse or for any damages resulting from the use of this tool.
