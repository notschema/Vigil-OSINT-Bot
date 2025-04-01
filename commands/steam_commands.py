"""
Steam lookup commands for Vigil OSINT Bot
"""

import datetime
import discord
import requests
import re
import logging
from discord.ext import commands

# Configure logging
logger = logging.getLogger("vigil_bot")

# Steam API constants
STEAM_API_BASE = "https://api.steampowered.com"
STEAM_PROFILE_BASE = "https://steamcommunity.com"

def register_steam_commands(bot, steam_api_key=None):
    """
    Register Steam-related commands with the bot
    
    Args:
        bot: The Discord bot instance
        steam_api_key: Optional Steam API key for enhanced lookups
    """
    
    # Check if API key is available
    has_api_key = steam_api_key is not None and steam_api_key.strip() != ""
    
    async def get_player_profile_without_api(steam_id):
        """
        Get a player's profile information without using the API
        
        Args:
            steam_id: Steam ID to lookup
            
        Returns:
            tuple: (success, profile_data_or_error_message)
        """
        try:
            profile_url = f"{STEAM_PROFILE_BASE}/profiles/{steam_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(profile_url, headers=headers)
            
            # Check if the profile exists
            if response.status_code != 200:
                return False, f"Error accessing profile: HTTP {response.status_code}"
            
            # Create a basic profile object
            profile = {
                "steamid": steam_id,
                "profileurl": profile_url,
                "communityvisibilitystate": 1,  # Assume private until we confirm it's public
            }
            
            # Extract username using different possible patterns
            username_patterns = [
                r'<span class="actual_persona_name">([^<]+)</span>',
                r'<div class="profile_header_centered(?:_persona)?"[^>]*>\s*<div[^>]*>\s*<span[^>]*>([^<]+)</span>',
                r'<title>Steam Community :: ([^<]+)</title>'
            ]
            
            for pattern in username_patterns:
                username_match = re.search(pattern, response.text)
                if username_match:
                    profile["personaname"] = username_match.group(1).strip()
                    break
            
            # Extract avatar
            avatar_patterns = [
                r'<div class="playerAvatarAutoSizeInner">\s*<img src="([^"]+)"',
                r'<div class="playerAvatar">\s*<img src="([^"]+)"',
                r'<div class="profile_avatar">\s*<img src="([^"]+)"'
            ]
            
            for pattern in avatar_patterns:
                avatar_match = re.search(pattern, response.text)
                if avatar_match:
                    profile["avatarfull"] = avatar_match.group(1)
                    break
            
            # Try to determine if the profile is public or private
            if "This profile is private" in response.text or "This profile is Friends Only" in response.text:
                profile["communityvisibilitystate"] = 1  # Private
            else:
                profile["communityvisibilitystate"] = 3  # Public
            
            # Try to extract country
            country_match = re.search(r'<div class="header_real_name ellipsis">[^<]*<bdi>(?:[^<]+)</bdi>[^<]*?(?:<img class="profile_flag" src="[^"]+/flags/([^.]+).gif")?', response.text)
            if country_match and country_match.group(1):
                profile["loccountrycode"] = country_match.group(1).upper()
            
            # Try to extract real name
            realname_match = re.search(r'<div class="header_real_name ellipsis">\s*<bdi>([^<]+)</bdi>', response.text)
            if realname_match:
                profile["realname"] = realname_match.group(1).strip()
            
            # Try to extract account creation date (this is often hidden but we'll try)
            creation_match = re.search(r'Member since ([^<]+)<', response.text)
            if creation_match:
                try:
                    # Try to parse the date string and convert to timestamp
                    date_str = creation_match.group(1).strip()
                    import time
                    from datetime import datetime
                    date_obj = datetime.strptime(date_str, "%B %d, %Y")
                    profile["timecreated"] = int(time.mktime(date_obj.timetuple()))
                except Exception as e:
                    logger.warning(f"Could not parse account creation date: {str(e)}")
            
            # Check if we could extract the username
            if "personaname" not in profile:
                logger.warning(f"Could not extract username from profile {steam_id}")
                # Use steam_id as fallback username
                profile["personaname"] = f"Steam User {steam_id}"
            
            return True, profile
        except Exception as e:
            logger.error(f"Error scraping player profile: {str(e)}")
            return False, f"Error accessing Steam profile: {str(e)}"
    
    async def get_steam_id(query):
        """
        Convert various Steam identifiers to a Steam ID
        
        Args:
            query: Can be a Steam ID, vanity URL name, or full profile URL
            
        Returns:
            tuple: (success, steam_id_or_error_message)
        """
        # Check if it's already a Steam ID (numeric only)
        if re.match(r'^\d+$', query):
            return True, query
            
        # Check if it's a full Steam profile URL
        url_match = re.match(r'https?://steamcommunity\.com/(?:id|profiles)/([^/]+)', query)
        if url_match:
            identifier = url_match.group(1)
            
            # Check if it's directly a numeric ID from the URL
            if re.match(r'^\d+$', identifier):
                return True, identifier
                
            # If it's a vanity URL, resolve it
            if has_api_key:
                try:
                    response = requests.get(
                        f"{STEAM_API_BASE}/ISteamUser/ResolveVanityURL/v1/",
                        params={
                            "key": steam_api_key,
                            "vanityurl": identifier
                        }
                    )
                    
                    # Check if the response is valid before parsing JSON
                    if response.status_code != 200:
                        logger.error(f"Steam API returned status code {response.status_code}")
                        return False, f"Steam API error (HTTP {response.status_code})"
                    
                    # Check if response has content
                    if not response.text:
                        logger.error("Empty response from Steam API")
                        return False, "Empty response from Steam API"
                    
                    # Try to parse the JSON response
                    try:
                        data = response.json()
                    except Exception as json_error:
                        logger.error(f"Failed to parse JSON from Steam API: {str(json_error)}")
                        logger.error(f"Response content: {response.text[:100]}...")
                        return False, "Invalid response from Steam API"
                    
                    if data.get("response", {}).get("success") == 1:
                        return True, data["response"]["steamid"]
                    else:
                        return False, f"Could not resolve vanity URL: {identifier}"
                except Exception as e:
                    logger.error(f"Error resolving vanity URL: {str(e)}")
                    return False, f"Error connecting to Steam API: {str(e)}"
            else:
                # Without API key, we'll use a profile page scraping approach
                try:
                    profile_url = f"{STEAM_PROFILE_BASE}/id/{identifier}"
                    response = requests.get(profile_url)
                    
                    # Check for a redirect, which might indicate a non-existent profile
                    if response.history and "error" in response.url:
                        return False, f"Profile not found: {identifier}"
                    
                    # Look for the SteamID in the page source using multiple patterns
                    # Pattern 1: Standard JavaScript variable
                    steam_id_match = re.search(r'g_steamID = "(\d+)";', response.text)
                    
                    if steam_id_match:
                        return True, steam_id_match.group(1)
                    
                    # Pattern 2: Profile data attribute
                    steam_id_match = re.search(r'data-steamid="(\d+)"', response.text)
                    
                    if steam_id_match:
                        return True, steam_id_match.group(1)
                    
                    # Pattern 3: miniprofile attribute (last resort)
                    steam_id_match = re.search(r'data-miniprofile="(\d+)"', response.text)
                    
                    if steam_id_match:
                        # Convert miniprofile ID to Steam ID (simplified approximation)
                        mini_id = int(steam_id_match.group(1))
                        # This is a rough approximation of how Steam calculates IDs
                        steam_id = "765" + str(1 + 2**32 + mini_id)
                        return True, steam_id
                        
                    # Pattern 4: Try checking if we're already redirected to a profile URL with numeric ID
                    if "/profiles/" in response.url:
                        profile_id_match = re.search(r'/profiles/(\d+)', response.url)
                        if profile_id_match:
                            return True, profile_id_match.group(1)
                    
                    return False, f"Could not extract Steam ID from profile page"
                except Exception as e:
                    logger.error(f"Error extracting Steam ID from profile: {str(e)}")
                    return False, f"Error accessing Steam profile: {str(e)}"
        
        # If it's just a vanity name without the URL, attempt to resolve it
        if has_api_key:
            try:
                response = requests.get(
                    f"{STEAM_API_BASE}/ISteamUser/ResolveVanityURL/v1/",
                    params={
                        "key": steam_api_key,
                        "vanityurl": query
                    }
                )
                
                # Check if the response is valid before parsing JSON
                if response.status_code != 200:
                    if response.status_code == 403:
                        logger.error(f"Steam API returned status code 403 - API key may be invalid or expired")
                        # Fall back to non-API method
                        logger.info(f"Falling back to web scraping method for vanity URL: {query}")
                        # Use alternative approach with direct web scraping
                        try:
                            profile_url = f"{STEAM_PROFILE_BASE}/id/{query}"
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                            }
                            response = requests.get(profile_url, headers=headers)
                            
                            # Check for a redirect, which might indicate a non-existent profile
                            if response.history and "error" in response.url:
                                return False, f"Profile not found: {query}"
                            
                            # Look for the SteamID in the page source
                            steam_id_match = re.search(r'g_steamID = "(\d+)";', response.text)
                            if steam_id_match:
                                return True, steam_id_match.group(1)
                            
                            return False, f"Could not extract Steam ID from profile page"
                        except Exception as e:
                            logger.error(f"Error extracting Steam ID from profile: {str(e)}")
                            return False, f"Error accessing Steam profile: {str(e)}"
                    else:
                        logger.error(f"Steam API returned status code {response.status_code}")
                        return False, f"Steam API error (HTTP {response.status_code})"
                
                # Check if response has content
                if not response.text:
                    logger.error("Empty response from Steam API")
                    return False, "Empty response from Steam API"
                
                # Try to parse the JSON response
                try:
                    data = response.json()
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON from Steam API: {str(json_error)}")
                    logger.error(f"Response content: {response.text[:100]}...")
                    return False, "Invalid response from Steam API"
                
                if data.get("response", {}).get("success") == 1:
                    return True, data["response"]["steamid"]
                else:
                    return False, f"Could not resolve vanity name: {query}"
            except Exception as e:
                logger.error(f"Error resolving vanity name: {str(e)}")
                return False, f"Error connecting to Steam API: {str(e)}"
        else:
            # Without API key, we'll use a profile page scraping approach
            try:
                profile_url = f"{STEAM_PROFILE_BASE}/id/{query}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(profile_url, headers=headers)
                
                # Check for a redirect, which might indicate a non-existent profile
                if response.history and "error" in response.url:
                    return False, f"Profile not found: {query}"
                
                # Look for the SteamID in the page source using multiple patterns
                # Pattern 1: Standard JavaScript variable
                steam_id_match = re.search(r'g_steamID = "(\d+)";', response.text)
                
                if steam_id_match:
                    return True, steam_id_match.group(1)
                
                # Pattern 2: Profile data attribute
                steam_id_match = re.search(r'data-steamid="(\d+)"', response.text)
                
                if steam_id_match:
                    return True, steam_id_match.group(1)
                
                # Pattern 3: miniprofile attribute (last resort)
                steam_id_match = re.search(r'data-miniprofile="(\d+)"', response.text)
                
                if steam_id_match:
                    # Convert miniprofile ID to Steam ID (simplified approximation)
                    mini_id = int(steam_id_match.group(1))
                    # This is a rough approximation of how Steam calculates IDs
                    steam_id = "765" + str(1 + 2**32 + mini_id)
                    return True, steam_id
                    
                # Pattern 4: Try checking if we're already redirected to a profile URL with numeric ID
                if "/profiles/" in response.url:
                    profile_id_match = re.search(r'/profiles/(\d+)', response.url)
                    if profile_id_match:
                        return True, profile_id_match.group(1)
                
                return False, f"Could not extract Steam ID from profile page"
            except Exception as e:
                logger.error(f"Error extracting Steam ID from profile: {str(e)}")
                return False, f"Error accessing Steam profile: {str(e)}"

    async def get_player_profile(steam_id):
        """
        Get a player's profile information
        
        Args:
            steam_id: Steam ID to lookup
            
        Returns:
            tuple: (success, profile_data_or_error_message)
        """
        if has_api_key:
            try:
                response = requests.get(
                    f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v2/",
                    params={
                        "key": steam_api_key,
                        "steamids": steam_id
                    }
                )
                
                # Check if the response is valid
                if response.status_code != 200:
                    if response.status_code == 403:
                        logger.error(f"Steam API returned status code 403 - API key may be invalid or expired")
                        # Fall back to non-API method
                        logger.info(f"Falling back to web scraping method for steam_id: {steam_id}")
                        return await get_player_profile_without_api(steam_id)
                    else:
                        logger.error(f"Steam API returned status code {response.status_code}")
                        return False, f"Steam API error (HTTP {response.status_code})"
                
                # Check if response has content
                if not response.text:
                    logger.error("Empty response from Steam API")
                    return False, "Empty response from Steam API"
                
                # Try to parse the JSON response
                try:
                    data = response.json()
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON from Steam API: {str(json_error)}")
                    logger.error(f"Response content: {response.text[:100]}...")
                    return False, "Invalid response from Steam API"
                
                if "response" in data and "players" in data["response"] and data["response"]["players"]:
                    return True, data["response"]["players"][0]
                else:
                    return False, "No player data found"
            except Exception as e:
                logger.error(f"Error fetching player profile: {str(e)}")
                return False, f"Error connecting to Steam API: {str(e)}"
        else:
            # Without API key, scrape the public profile page
            try:
                profile_url = f"{STEAM_PROFILE_BASE}/profiles/{steam_id}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(profile_url, headers=headers)
                
                # Check if the profile exists
                if response.status_code != 200:
                    return False, f"Error accessing profile: HTTP {response.status_code}"
                
                # Create a basic profile object
                profile = {
                    "steamid": steam_id,
                    "profileurl": profile_url,
                    "communityvisibilitystate": 1,  # Assume private until we confirm it's public
                }
                
                # Extract username using different possible patterns
                username_patterns = [
                    r'<span class="actual_persona_name">([^<]+)</span>',
                    r'<div class="profile_header_centered(?:_persona)?"[^>]*>\s*<div[^>]*>\s*<span[^>]*>([^<]+)</span>',
                    r'<title>Steam Community :: ([^<]+)</title>'
                ]
                
                for pattern in username_patterns:
                    username_match = re.search(pattern, response.text)
                    if username_match:
                        profile["personaname"] = username_match.group(1).strip()
                        break
                
                # Extract avatar
                avatar_patterns = [
                    r'<div class="playerAvatarAutoSizeInner">\s*<img src="([^"]+)"',
                    r'<div class="playerAvatar">\s*<img src="([^"]+)"',
                    r'<div class="profile_avatar">\s*<img src="([^"]+)"'
                ]
                
                for pattern in avatar_patterns:
                    avatar_match = re.search(pattern, response.text)
                    if avatar_match:
                        profile["avatarfull"] = avatar_match.group(1)
                        break
                
                # Try to determine if the profile is public or private
                if "This profile is private" in response.text or "This profile is Friends Only" in response.text:
                    profile["communityvisibilitystate"] = 1  # Private
                else:
                    profile["communityvisibilitystate"] = 3  # Public
                
                # Try to extract country
                country_match = re.search(r'<div class="header_real_name ellipsis">[^<]*<bdi>(?:[^<]+)</bdi>[^<]*?(?:<img class="profile_flag" src="[^"]+/flags/([^.]+).gif")?', response.text)
                if country_match and country_match.group(1):
                    profile["loccountrycode"] = country_match.group(1).upper()
                
                # Try to extract real name
                realname_match = re.search(r'<div class="header_real_name ellipsis">\s*<bdi>([^<]+)</bdi>', response.text)
                if realname_match:
                    profile["realname"] = realname_match.group(1).strip()
                
                # Check if we could extract the username
                if "personaname" not in profile:
                    logger.warning(f"Could not extract username from profile {steam_id}")
                    # Use steam_id as fallback username
                    profile["personaname"] = f"Steam User {steam_id}"
                
                return True, profile
            except Exception as e:
                logger.error(f"Error scraping player profile: {str(e)}")
                return False, f"Error accessing Steam profile: {str(e)}"
    
    async def get_player_games(steam_id):
        """
        Get a player's owned games
        
        Args:
            steam_id: Steam ID to lookup
            
        Returns:
            tuple: (success, games_data_or_error_message)
        """
        nonlocal has_api_key
        
        if has_api_key:
            try:
                response = requests.get(
                    f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v1/",
                    params={
                        "key": steam_api_key,
                        "steamid": steam_id,
                        "include_appinfo": 1,
                        "include_played_free_games": 1
                    }
                )
                
                # Check if the response is valid
                if response.status_code != 200:
                    if response.status_code == 403:
                        logger.error(f"Steam API returned status code 403 - API key may be invalid or expired")
                        logger.info(f"Switching to non-API mode for all future requests")
                        # Set has_api_key to False to prevent further API calls
                        has_api_key = False
                        # Fall back to web scraping for this profile
                        return await get_player_profile_without_api(steam_id)
                    else:
                        logger.error(f"Steam API returned status code {response.status_code}")
                        return False, f"Steam API error (HTTP {response.status_code})"
                
                # Check if response has content
                if not response.text:
                    logger.error("Empty response from Steam API")
                    return False, "Empty response from Steam API"
                
                # Try to parse the JSON response
                try:
                    data = response.json()
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON from Steam API: {str(json_error)}")
                    logger.error(f"Response content: {response.text[:100]}...")
                    return False, "Invalid response from Steam API"
                
                if "response" in data and "games" in data["response"]:
                    return True, data["response"]
                else:
                    return False, "No games data found or profile is private"
            except Exception as e:
                logger.error(f"Error fetching player games: {str(e)}")
                return False, f"Error connecting to Steam API: {str(e)}"
        else:
            return False, "API key required to fetch games list"
    
    async def get_player_friends(steam_id):
        """
        Get a player's friend list
        
        Args:
            steam_id: Steam ID to lookup
            
        Returns:
            tuple: (success, friends_data_or_error_message)
        """
        if has_api_key:
            try:
                response = requests.get(
                    f"{STEAM_API_BASE}/ISteamUser/GetFriendList/v1/",
                    params={
                        "key": steam_api_key,
                        "steamid": steam_id,
                        "relationship": "friend"
                    }
                )
                
                # Check if the response is valid
                if response.status_code != 200:
                    # Note: 401 is common for private profiles
                    if response.status_code == 401:
                        return False, "Friend list is private or not available"
                    logger.error(f"Steam API returned status code {response.status_code}")
                    return False, f"Steam API error (HTTP {response.status_code})"
                
                # Check if response has content
                if not response.text:
                    logger.error("Empty response from Steam API")
                    return False, "Empty response from Steam API"
                
                # Try to parse the JSON response
                try:
                    data = response.json()
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON from Steam API: {str(json_error)}")
                    logger.error(f"Response content: {response.text[:100]}...")
                    return False, "Invalid response from Steam API"
                
                if "friendslist" in data and "friends" in data["friendslist"]:
                    return True, data["friendslist"]["friends"]
                else:
                    return False, "No friends data found or profile is private"
            except Exception as e:
                logger.error(f"Error fetching player friends: {str(e)}")
                return False, f"Error connecting to Steam API: {str(e)}"
        else:
            return False, "API key required to fetch friends list"
    
    async def get_player_bans(steam_id):
        """
        Get a player's ban status
        
        Args:
            steam_id: Steam ID to lookup
            
        Returns:
            tuple: (success, bans_data_or_error_message)
        """
        if has_api_key:
            try:
                response = requests.get(
                    f"{STEAM_API_BASE}/ISteamUser/GetPlayerBans/v1/",
                    params={
                        "key": steam_api_key,
                        "steamids": steam_id
                    }
                )
                
                # Check if the response is valid
                if response.status_code != 200:
                    logger.error(f"Steam API returned status code {response.status_code}")
                    return False, f"Steam API error (HTTP {response.status_code})"
                
                # Check if response has content
                if not response.text:
                    logger.error("Empty response from Steam API")
                    return False, "Empty response from Steam API"
                
                # Try to parse the JSON response
                try:
                    data = response.json()
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON from Steam API: {str(json_error)}")
                    logger.error(f"Response content: {response.text[:100]}...")
                    return False, "Invalid response from Steam API"
                
                if "players" in data and data["players"]:
                    return True, data["players"][0]
                else:
                    return False, "No ban data found"
            except Exception as e:
                logger.error(f"Error fetching player bans: {str(e)}")
                return False, f"Error connecting to Steam API: {str(e)}"
        else:
            return False, "API key required to fetch ban information"
    
    @bot.command(name="steam", aliases=["steamlookup", "steamid"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def steam_lookup(ctx, *, query: str):
        """
        Look up a Steam profile by username, URL, or Steam ID
        
        Usage:
        !steam <username, URL, or Steam ID>
        
        Examples:
        !steam 76561198012345678
        !steam gaben
        !steam https://steamcommunity.com/id/gaben
        """
        nonlocal has_api_key
        
        # Log the API key status (without revealing the key itself)
        if has_api_key:
            logger.info("Steam lookup using API key")
        else:
            logger.info("Steam lookup in limited mode (no API key)")
        
        # Send initial message with API status indicator
        if has_api_key:
            message = await ctx.send(f"🔍 Looking up Steam profile for `{query}`...")
        else:
            message = await ctx.send(f"🔍 Looking up Steam profile for `{query}` (limited mode - no API key)...")
        
        try:
            # Convert query to Steam ID
            success, result = await get_steam_id(query)
            if not success:
                await message.edit(content=f"❌ Error: {result}")
                return
            
            steam_id = result
            logger.info(f"Resolved Steam ID: {steam_id} for query: {query}")
            
            # Fetch the profile data
            profile_success, profile_data = await get_player_profile(steam_id)
            if not profile_success:
                await message.edit(content=f"❌ Error: {profile_data}")
                return
                
            logger.info(f"Successfully fetched profile data for Steam ID: {steam_id}")
            
            # Create embed for the profile
            embed = discord.Embed(
                title=profile_data.get("personaname", "Unknown"),
                url=profile_data.get("profileurl", f"{STEAM_PROFILE_BASE}/profiles/{steam_id}"),
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            
            # Set thumbnail to avatar if available
            if "avatarfull" in profile_data:
                embed.set_thumbnail(url=profile_data["avatarfull"])
            
            # Add Steam ID
            embed.add_field(
                name="Steam ID",
                value=f"`{steam_id}`",
                inline=True
            )
            
            # Check if profile is public
            if "communityvisibilitystate" in profile_data:
                visibility = "Public" if profile_data["communityvisibilitystate"] == 3 else "Private"
                embed.add_field(
                    name="Profile Visibility",
                    value=visibility,
                    inline=True
                )
            
            # Add account creation date if available
            if "timecreated" in profile_data:
                created_date = datetime.datetime.fromtimestamp(profile_data["timecreated"])
                embed.add_field(
                    name="Account Created",
                    value=created_date.strftime("%Y-%m-%d"),
                    inline=True
                )
            
            # Add last online time if available
            if "lastlogoff" in profile_data:
                last_online = datetime.datetime.fromtimestamp(profile_data["lastlogoff"])
                embed.add_field(
                    name="Last Online",
                    value=last_online.strftime("%Y-%m-%d %H:%M:%S"),
                    inline=True
                )
            
            # Add country if available
            if "loccountrycode" in profile_data:
                embed.add_field(
                    name="Country",
                    value=f":flag_{profile_data['loccountrycode'].lower()}:",
                    inline=True
                )
            
            # Add real name if available
            if "realname" in profile_data and profile_data["realname"]:
                embed.add_field(
                    name="Real Name",
                    value=profile_data["realname"],
                    inline=True
                )
            
            # Fetch ban information if API key is available
            if has_api_key:
                ban_success, ban_data = await get_player_bans(steam_id)
                if ban_success:
                    ban_info = []
                    
                    if ban_data.get("CommunityBanned"):
                        ban_info.append("Community Ban")
                    
                    if ban_data.get("VACBanned"):
                        vac_ban_count = ban_data.get("NumberOfVACBans", 0)
                        vac_ban_days = ban_data.get("DaysSinceLastBan", 0)
                        ban_info.append(f"VAC Bans: {vac_ban_count} ({vac_ban_days} days since last)")
                    
                    if ban_data.get("EconomyBan") and ban_data.get("EconomyBan") != "none":
                        ban_info.append(f"Economy Ban: {ban_data.get('EconomyBan')}")
                    
                    if ban_data.get("NumberOfGameBans", 0) > 0:
                        ban_info.append(f"Game Bans: {ban_data.get('NumberOfGameBans')}")
                    
                    if ban_info:
                        embed.add_field(
                            name="Ban Status",
                            value="\n".join(ban_info),
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="Ban Status",
                            value="No bans on record",
                            inline=False
                        )
            
            # Fetch game information if API key is available and profile is public
            if has_api_key and profile_data.get("communityvisibilitystate") == 3:
                games_success, games_data = await get_player_games(steam_id)
                if games_success:
                    game_count = games_data.get("game_count", 0)
                    
                    # Calculate total playtime
                    total_playtime = sum(game.get("playtime_forever", 0) for game in games_data.get("games", []))
                    total_playtime_hours = round(total_playtime / 60, 1)
                    
                    # Get top 5 most played games
                    if "games" in games_data:
                        top_games = sorted(
                            games_data["games"], 
                            key=lambda x: x.get("playtime_forever", 0), 
                            reverse=True
                        )[:5]
                        
                        embed.add_field(
                            name=f"Game Stats ({game_count} games, {total_playtime_hours} hours)",
                            value="\n".join([
                                f"{game.get('name', 'Unknown')}: {round(game.get('playtime_forever', 0) / 60, 1)} hours"
                                for game in top_games
                            ]) if top_games else "No game data available",
                            inline=False
                        )
            
            # Fetch friends if API key is available and profile is public
            if has_api_key and profile_data.get("communityvisibilitystate") == 3:
                friends_success, friends_data = await get_player_friends(steam_id)
                if friends_success:
                    friend_count = len(friends_data)
                    embed.add_field(
                        name="Friends",
                        value=f"{friend_count} friends on Steam",
                        inline=True
                    )
            
            # Set footer with API status information
            if has_api_key:
                embed.set_footer(text="Vigil OSINT Bot • Steam Lookup (Full API Access)")
            else:
                embed.set_footer(text="Vigil OSINT Bot • Steam Lookup (Limited Mode - No API Key)")
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
            
        except Exception as e:
            logger.error(f"Error in Steam lookup: {str(e)}")
            await message.edit(content=f"❌ Error looking up Steam profile: {str(e)}")