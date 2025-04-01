#!/bin/bash
# This script sets up the external tools needed by VigilBot

# Create necessary directories
mkdir -p temp logs config

echo "Setting up external OSINT tools..."

# Setup Sherlock (if it doesn't exist)
if [ ! -d "sherlock" ]; then
    echo "Installing Sherlock..."
    git clone https://github.com/sherlock-project/sherlock.git
    cd sherlock
    pip install -r requirements.txt
    cd ..
fi

# Setup Maigret (if needed)
if [ ! -f "Maigret/data/data.json" ]; then
    echo "Setting up Maigret..."
    # If Maigret is already cloned but missing data
    if [ -d "Maigret" ]; then
        cd Maigret
        python3 utils/generate_sites.py
        mv generated_data/sites.json data/data.json
        cd ..
    else
        # Full install of Maigret
        git clone https://github.com/soxoj/maigret.git Maigret
        cd Maigret
        pip install -e .
        python3 utils/generate_sites.py
        mv generated_data/sites.json data/data.json
        cd ..
    fi
fi

# Setup holehe if needed
if [ ! -d "holehe" ]; then
    echo "Installing holehe..."
    git clone https://github.com/megadose/holehe.git
    cd holehe
    pip install -e .
    cd ..
fi

echo "Tool setup complete!"
