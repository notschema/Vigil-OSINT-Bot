#!/bin/bash
# Script to set up the .env file for VigilBot in Unraid

# Make sure we're working in the right directory
cd "$(dirname "$0")"

# Check if .env exists in current directory
if [ ! -f ".env" ]; then
  echo "Error: .env file not found in current directory."
  echo "Please make sure your .env file with the Discord token exists."
  exit 1
fi

# Create the appdata directory if it doesn't exist
mkdir -p /mnt/user/appdata/vigilbot/

# Copy the .env file to the appdata directory
echo "Copying .env file to /mnt/user/appdata/vigilbot/.env"
cp .env /mnt/user/appdata/vigilbot/.env

# Set proper permissions
echo "Setting permissions for .env file"
chmod 644 /mnt/user/appdata/vigilbot/.env

# Create other required directories
mkdir -p /mnt/user/appdata/vigilbot/config
mkdir -p /mnt/user/appdata/vigilbot/logs
mkdir -p /mnt/user/appdata/vigilbot/temp

# Set permissions for directories
chmod -R 755 /mnt/user/appdata/vigilbot/config
chmod -R 755 /mnt/user/appdata/vigilbot/logs
chmod -R 755 /mnt/user/appdata/vigilbot/temp

echo "Setup complete. Now you can restart the containers with:"
echo "docker-compose -f docker-compose.unraid.yml down"
echo "docker-compose -f docker-compose.unraid.yml up -d"
