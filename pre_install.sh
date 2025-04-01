#!/bin/bash
# This script prepares the environment for successful package installation

echo "Updating pip and installing essential build tools..."
pip install --upgrade pip wheel setuptools

echo "Installing critical dependencies with pre-built wheels..."
# Install these packages with pre-built wheels first to avoid compilation issues
pip install yarl==1.9.4 --only-binary=:all:
pip install aiohttp==3.8.5 --only-binary=:all:
pip install reportlab==3.6.12 --only-binary=:all:

# Create required Python header directories
echo "Setting up Python development environment..."
mkdir -p /usr/local/include/python3.11

echo "Pre-installation preparation completed"
