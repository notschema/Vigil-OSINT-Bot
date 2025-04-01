#!/bin/bash
# This script installs maigret with specific dependency handling

echo "Installing pre-built packages..."
# Use pre-built wheels for problematic packages
pip install --upgrade pip wheel setuptools

# Install problematic packages first with pre-built wheels
pip install reportlab==3.6.12
pip install aiohttp==3.8.5
pip install yarl==1.9.4

# Now install maigret with --no-dependencies flag
echo "Installing maigret without dependencies..."
pip install --no-deps maigret==0.4.4

# Install additional dependencies needed by maigret
echo "Installing maigret dependencies..."
pip install aiodns==3.0.0 async-timeout==4.0.2 attrs==22.1.0 chardet==5.0.0 idna==3.3 lxml==4.9.1 multidict==6.0.2 six==1.16.0
pip install arabic-reshaper==2.1.3 future==0.18.2 future-annotations==1.0.0 html5lib==1.1 Jinja2==3.1.2 MarkupSafe==2.1.1 mock==4.0.3 
pip install PyPDF2==2.10.4 python-bidi==0.4.2 socid-extractor>=0.0.21 soupsieve==2.3.2.post1 typing-extensions==4.3.0 webencodings==0.5.1
pip install xhtml2pdf==0.2.8 XMind==1.2.0 networkx==2.5.1 pyvis==0.2.1

# Install additional web scraping dependencies
echo "Installing web scraping dependencies..."
pip install cloudscraper requests-random-user-agent

echo "Maigret installation completed"
