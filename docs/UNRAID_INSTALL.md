# VigilBot Unraid Installation Guide

This guide will walk you through setting up VigilBot on your Unraid server using Docker.

> **New Feature:** VigilBot now includes a modern React/Next.js dashboard that allows you to start/stop the bot and view the console output in real-time with a beautiful, responsive interface.

## Prerequisites

- Unraid server (6.8.0 or later)
- Docker and Docker Compose installed on your Unraid server
- Community Applications plugin installed (recommended)
- Git installed (can be installed via NerdTools)

## Installation Steps

### 1. Clone the Repository

First, SSH into your Unraid server:

```bash
ssh root@your-unraid-ip
```

Navigate to your preferred location for Docker application data:

```bash
cd /mnt/user/appdata/
```

Clone the VigilBot repository:

```bash
git clone https://github.com/notschema/Vigil_OSINT_Bot.git vigilbot
cd vigilbot
```

### 2. Configure Environment Variables

Create and edit the `.env` file:

```bash
nano .env
```

Add your Discord Bot Token and other required configuration:

```
# Vigil OSINT Bot Environment Variables
# Store your tokens and API keys here

# Discord Bot Token (REQUIRED) - Get this from Discord Developer Portal
DISCORD_TOKEN=your_discord_token_here

# GitHub API Token (OPTIONAL) - Increases rate limits for GitHub API requests
GITHUB_TOKEN=your_github_token_here

# CheckLeaked API Token - For breach data search functionality (!breach, !breachx, !crackhash)
CHECKLEAKED_TOKEN=your_checkleaked_token_here

# Steam API Key (OPTIONAL) - Get from https://steamcommunity.com/dev/apikey
STEAM_API_KEY=your_steam_api_key_here

# Admin User IDs - Comma-separated list of Discord user IDs for admin commands
ADMIN_IDS=your_discord_id_here
```

Save and exit the editor (Ctrl+X, then Y, then Enter in nano).

### 3. Set Permissions

Make the startup script executable:

```bash
chmod +x start.sh
```

### 4. Build and Start the Docker Container

Use Docker Compose to build and start the container:

```bash
docker-compose -f docker-compose.unraid.yml up -d
```

### 5. Access the Web Interface

Once the container is running, you can access the web interface at:

```
http://your-unraid-ip:8080
```

The React dashboard provides:
- Beautiful, responsive UI with light/dark mode
- Start/stop/restart controls for the bot
- Real-time console output via WebSocket connection
- Status monitoring with animations and visual feedback
- Smooth transitions and modern UI elements

The API backend runs on:

```
http://your-unraid-ip:8000
```

### 6. Verify Installation

Check if the container is running:

```bash
docker ps | grep vigilbot
```

View logs to ensure everything is working properly:

```bash
docker logs vigilbot
```

## Setting Up Unraid Docker Template (Optional)

For easier management through the Unraid GUI:

1. In the Unraid web interface, go to the Docker tab
2. Click "Add Container"
3. Fill in the following:
   - Name: vigilbot
   - Repository: Custom, point to your local Dockerfile location
   - Network Type: Bridge
   - Port Mappings:
     - Host Port: `8000`, Container Port: `8000`, Type: `TCP` (API)
     - Host Port: `8080`, Container Port: `8080`, Type: `TCP` (Frontend)
   - Add the following paths:
     - Host Path: `/mnt/user/appdata/vigilbot/config`, Container Path: `/app`
     - Host Path: `/mnt/user/appdata/vigilbot/logs`, Container Path: `/app/logs`
     - Host Path: `/mnt/user/appdata/vigilbot/temp`, Container Path: `/app/temp`
     - Host Path: `/mnt/user/appdata/vigilbot/api`, Container Path: `/app/api`
     - Host Path: `/mnt/user/appdata/vigilbot/frontend`, Container Path: `/app/frontend`
   - Add environment variables from your .env file
   - Add these additional environment variables:
     - API_PORT=8000
     - FRONTEND_PORT=8080
     - NEXT_PUBLIC_API_URL=http://localhost:8000
     - NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

## Using a Reverse Proxy

If you want to access the web interface through a domain name, add the following to your reverse proxy configuration (NGINX example):

```nginx
# API Backend
server {
    listen 80;
    server_name api.vigilbot.yourdomain.com;

    location / {
        proxy_pass http://your-unraid-ip:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # WebSocket support (needed for real-time console)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Frontend
server {
    listen 80;
    server_name vigilbot.yourdomain.com;

    location / {
        proxy_pass http://your-unraid-ip:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Auto-Starting at Boot

The container is configured to restart unless explicitly stopped (`restart: unless-stopped`), which means it will start automatically when Unraid boots up.

## Conclusion

Your VigilBot should now be running on your Unraid server in a Docker container with a modern React/Next.js dashboard. You can:

1. Access the React dashboard at `http://your-unraid-ip:8080`
2. Start/stop/restart the bot through the beautiful UI
3. View the console output in real-time with WebSocket updates
4. Monitor the bot's status with animated visual indicators
5. Toggle between light and dark themes

The bot will automatically start when your Unraid server boots up and can be managed through the React dashboard, the API, or Unraid's Docker interface.