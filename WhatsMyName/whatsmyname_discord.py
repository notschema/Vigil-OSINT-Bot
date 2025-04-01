# WhatsMyName integration for Discord bots
import json
import asyncio
import aiohttp

# WhatsMyName data URL and headers
WMN_URL = "https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json"
WMN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# Check a single site for username existence
async def check_site(session, site, username):
    try:
        # Replace the username placeholder in the URL
        check_url = site["uri_check"].replace("{account}", username)
        
        # Make the request
        async with session.get(check_url, headers=WMN_HEADERS, timeout=10) as response:
            # Get the response text
            text = await response.text()
            
            # Check if the response matches the expected status code and contains the expected string
            if response.status == site["e_code"] and site["e_string"] in text:
                return site["name"], check_url
    except Exception as e:
        print(f"Error checking {site['name']}: {e}")
    
    return None

# Check username existence across multiple sites
async def check_username_existence(username, data):
    found_sites = []
    
    # Create a client session for making requests
    async with aiohttp.ClientSession() as session:
        # Create tasks for checking each site
        tasks = []
        for site in data["sites"]:
            # Skip sites that don't have the necessary fields
            if not all(field in site for field in ["uri_check", "e_code", "e_string"]):
                continue
                
            # Create a task for checking this site
            task = asyncio.create_task(check_site(session, site, username))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        for result in results:
            if isinstance(result, tuple):
                found_sites.append(result)
    
    return found_sites
