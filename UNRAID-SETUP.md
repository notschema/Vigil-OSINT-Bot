# VigilBot Setup on Unraid

This guide will help you set up VigilBot on your Unraid server.

## Prerequisites

1. Unraid server with Docker installed
2. A valid Discord bot token (from the Discord Developer Portal)

## Setup Instructions

### 1. Prepare the Environment File

The most important file for the bot is the `.env` file which contains your Discord token. This file must be properly placed for the bot to work.

- Make sure you have a valid `.env` file in the same directory as your docker-compose file. At minimum, it should contain:
  ```
  DISCORD_TOKEN=your_discord_token_here
  ```

### 2. Set Up Directories

Run the included setup script to create necessary directories and copy your .env file to the correct location:

```bash
chmod +x setup_env.sh
./setup_env.sh
```

This script will:
- Copy your .env file to `/mnt/user/appdata/vigilbot/.env`
- Create required directories in `/mnt/user/appdata/vigilbot/`
- Set proper permissions

### 3. Start the Containers

Start the containers using docker-compose:

```bash
docker-compose -f docker-compose.unraid.yml up -d
```

### 4. Verify the Services

Check if both services are running:

```bash
docker ps | grep vigilbot
```

You should see both `vigilbot-api` and `vigilbot-frontend` containers running.

### 5. Check the Logs

If the bot isn't connecting to Discord, check the logs:

```bash
docker logs vigilbot-api
```

Or check the detailed bot logs:

```bash
docker exec vigilbot-api cat /app/logs/vigil_bot.log
```

## Troubleshooting

### Bot Not Starting

If the API starts but the bot doesn't connect to Discord:

1. Verify the .env file is properly mounted:
   ```bash
   docker exec vigilbot-api cat /app/.env
   ```
   
2. Check if the Discord token is valid:
   ```bash
   docker exec vigilbot-api grep DISCORD_TOKEN /app/.env
   ```

3. Manually start the bot from the API:
   ```bash
   docker exec vigilbot-api curl -X POST http://localhost:8000/start
   ```

### API Not Starting

If the API doesn't start:

1. Check container logs:
   ```bash
   docker logs vigilbot-api
   ```

2. Verify all required directories exist and have correct permissions:
   ```bash
   ls -la /mnt/user/appdata/vigilbot/
   ```

## Access

- API: `http://your_server_ip:1337`
- Frontend: `http://your_server_ip:1338`

## Restarting the Bot

If you need to restart just the bot without restarting the container:

```bash
docker exec vigilbot-api curl -X POST http://localhost:8000/restart
```