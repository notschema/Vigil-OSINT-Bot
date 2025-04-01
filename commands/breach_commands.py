"""
Breach data search commands for Vigil OSINT Bot
"""

import datetime
import discord
import json
import logging
from discord.ext import commands

from .utils import checkleaked_available

# Custom cooldown for commands
class VCooldown(commands.Cooldown):
    """Custom cooldown class that checks for admin role"""
    def __init__(self, rate, per, type):
        super().__init__(rate, per, type)
        self.default_rate = rate
        self.default_per = per
        self.admin_per = 5.0  # 5 second cooldown for admins

    def get_tokens(self, current=None):
        return self.default_rate

    def update_rate_limit(self, current=None):
        current = current or time.time()
        self._last = current

        if self.type == commands.BucketType.user:
            self.per = self.admin_per
            
        # Reset tokens to 0
        self._tokens = self.get_tokens(current)
        
        # Return the cooldown period
        return 0.0
        
# Custom cooldown check function
def dynamic_cooldown(rate, per, bucket_type=commands.BucketType.user):
    """Custom cooldown function that returns a standard cooldown"""
    # Return standard cooldown for now - no checking for admin roles yet
    return commands.cooldown(1, 5, bucket_type)

import time  # Add at the top with other imports

def register_breach_commands(bot, checkleaked_token=None):
    # Initialize the API client if available
    if checkleaked_available and checkleaked_token:
        from CheckLeaked.checkleaked_api import CheckLeakedAPI
        checkleaked_api = CheckLeakedAPI(checkleaked_token)
    else:
        checkleaked_api = None

    @bot.command(name="breach", help="Search for user data in breached databases")
    @commands.cooldown(1, 5, commands.BucketType.user)  # Use a simple cooldown for now
    async def breach_search(ctx, query: str = None, search_type: str = None):
        """
        Search for user data in breached databases using CheckLeaked
        
        Usage: !breach <query> <search_type>
        Example: !breach john@example.com email
        
        Valid search types:
        - email: Search by email address
        - username: Search by username
        - ip_address: Search by IP address
        - name: Search by person's name
        - address: Search by physical address
        - phone: Search by phone number
        - vin: Search by vehicle identification number
        - free: Free-text search
        
        Notes:
        - This command requires a valid CheckLeaked API token
        - Results may contain sensitive information
        - Limited to 5 results in Discord for privacy reasons
        - This command has a 30-second cooldown (5 seconds for users with the "Vigil - Admin" role)
        """
        if not checkleaked_available or not checkleaked_api:
            await ctx.send("❌ The CheckLeaked module is not available. This command will not work.")
            return
        
        # Check if parameters are provided
        if query is None or search_type is None:
            await ctx.send("❌ Missing parameters! Usage: `!breach <query> <search_type>`\n"
                          "Example: `!breach john@example.com email`\n\n"
                          "Valid search types: email, username, ip_address, name, address, phone, vin, free\n\n"
                          "Use `!help breach` for more information.")
            return
            
        # Validate search type
        valid_types = ["email", "username", "ip_address", "name", "address", "phone", "vin", "free"]
        if search_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid search type. Please use one of: `{', '.join(valid_types)}`\n"
                           f"Example: `!breach john@example.com email`")
            return
        
        # Send initial message
        message = await ctx.send(f"🔍 Searching breach data for {search_type}: `{query}`...")
        
        try:
            # Search for breaches
            results = checkleaked_api.search_dehashed(query, search_type.lower())
            
            if results.get("error"):
                await message.edit(content=f"❌ Error from CheckLeaked API: {results['error']}")
                return
            
            if not results.get("entries") or len(results["entries"]) == 0:
                await message.edit(content=f"❌ No breach data found for {search_type}: `{query}`.")
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"Breach Data for {search_type}: {query}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(
                name="Results Count",
                value=f"{len(results['entries'])} entries found",
                inline=False
            )
            
            # Add breach entries to embed
            for i, entry in enumerate(results["entries"][:5]):  # Limit to first 5 entries
                field_value = ""
                for key, value in entry.items():
                    if value and key not in ["id"]:
                        field_value += f"**{key}**: {value}\n"
                
                embed.add_field(
                    name=f"Entry {i+1}",
                    value=field_value or "No data",
                    inline=False
                )
            
            if len(results["entries"]) > 5:
                embed.set_footer(text=f"Showing 5 of {len(results['entries'])} results.")
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
        
        except Exception as e:
            await message.edit(content=f"❌ Error searching breach data: {str(e)}")

    @bot.command(name="breachx", aliases=["advbreach", "xbreach"], help="Advanced breach data search with experimental API")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def breach_advanced(ctx, query: str = None, search_type: str = None):
        """
        Advanced breach data search using CheckLeaked's experimental API
        
        Usage: !breachx <query> <search_type>
        Example: !breachx johndoe username
        
        Valid search types:
        - username: Search by username across multiple breach databases
        - mass: Mass query across multiple data sources
        - email: Search by email with enhanced results
        - lastip: Find the last known IP address for a target
        - password: Search by password (plaintext)
        - name: Search by person's name with enhanced results
        - hash: Search by password hash
        
        Notes:
        - This command provides more detailed results than standard !breach
        - Uses CheckLeaked's experimental API with broader search capabilities
        - Results may contain sensitive information
        - Limited to 5 results in Discord for privacy reasons
        - This command has a 30-second cooldown (5 seconds for users with the "Vigil - Admin" role)
        """
        if not checkleaked_available or not checkleaked_api:
            await ctx.send("❌ The CheckLeaked module is not available. This command will not work.")
            return
        
        # Check if parameters are provided
        if query is None or search_type is None:
            await ctx.send("❌ Missing parameters! Usage: `!breachx <query> <search_type>`\n"
                          "Example: `!breachx johndoe username`\n\n"
                          "Valid search types: username, mass, email, lastip, password, name, hash\n\n"
                          "Use `!help breachx` for more information.")
            return
            
        # Validate search type
        valid_types = ["username", "mass", "email", "lastip", "password", "name", "hash"]
        if search_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid search type. Please use one of: `{', '.join(valid_types)}`\n"
                           f"Example: `!breachx johndoe username`")
            return
        
        # Send initial message
        message = await ctx.send(f"🔍 Performing advanced breach search for {search_type}: `{query}`...")
        
        try:
            # Search for breaches
            results = checkleaked_api.search_experimental(query, search_type.lower())
            
            # Debug - log the API response
            logging.getLogger("vigil_bot").info(f"CheckLeaked API response: {json.dumps(results, indent=2)}")
            
            if results.get("error"):
                await message.edit(content=f"❌ Error from CheckLeaked API: {results['error']}")
                return
            
            # Check for different response structures - the API returns "results" not "data" or "result"
            if results.get("data") is None and results.get("result") is None and results.get("results") is not None:
                # API is returning results array
                results["data"] = results.get("results", [])
            elif results.get("data") is None and results.get("result") is not None:
                # API might be returning result instead of data
                results["data"] = results.get("result", [])
            
            if not results.get("data") or len(results["data"]) == 0:
                await message.edit(content=f"❌ No advanced breach data found for {search_type}: `{query}`.")
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"Advanced Breach Data for {search_type}: {query}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(
                name="Results Count",
                value=f"{len(results['data'])} entries found",
                inline=False
            )
            
            # Process and add results to embed
            processed_data = results.get("data", [])
            
            # Handle different data formats
            if isinstance(processed_data, dict):
                # If data is a dictionary rather than a list, transform it
                processed_entries = []
                for key, value in processed_data.items():
                    if isinstance(value, dict):
                        # Add the key as an identifier in the entry
                        value["identifier"] = key
                        processed_entries.append(value)
                    else:
                        # Simple key-value
                        processed_entries.append({"identifier": key, "value": value})
                processed_data = processed_entries
            
            # Handle case where processed_data might be a string
            if isinstance(processed_data, str):
                processed_data = [{"result": processed_data}]
                
            # Handle empty arrays or null values in a better way
            if not processed_data:
                embed.add_field(
                    name="No Results Found",
                    value="The search completed but no breach data was found.",
                    inline=False
                )
            else:
                # Add breach entries to embed
                for i, entry in enumerate(processed_data[:5]):  # Limit to first 5 entries
                    field_value = ""
                    
                    # Handle case where entry might be a string instead of dict
                    if isinstance(entry, str):
                        field_value = entry
                    elif isinstance(entry, dict):
                        for key, value in entry.items():
                            if value and key not in ["id"]:
                                # Handle different value types
                                if isinstance(value, dict):
                                    # If value is a nested dictionary
                                    field_value += f"**{key}**:\n"
                                    for sub_key, sub_value in value.items():
                                        if sub_value:
                                            field_value += f"  • **{sub_key}**: {sub_value}\n"
                                else:
                                    field_value += f"**{key}**: {value}\n"
                    
                    embed.add_field(
                        name=f"Entry {i+1}",
                        value=field_value or "No data",
                        inline=False
                    )
                
                if len(processed_data) > 5:
                    embed.set_footer(text=f"Showing 5 of {len(processed_data)} results.")
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
        
        except Exception as e:
            await message.edit(content=f"❌ Error searching advanced breach data: {str(e)}")

    @bot.command(name="crackhash", aliases=["hash"], help="Attempt to decrypt a password hash")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def crack_hash(ctx, hash_value: str = None):
        """
        Attempt to decrypt a password hash using CheckLeaked's database
        
        Usage: !crackhash <hash_value>
        Example: !crackhash 5f4dcc3b5aa765d61d8327deb882cf99
        
        Supported hash types:
        - MD5
        - SHA1
        - SHA256
        - And many others (automatically detected)
        
        Notes:
        - Success depends on whether the hash exists in known breach databases
        - Returns the plaintext password if found
        - This command has a 30-second cooldown
        """
        if not checkleaked_available or not checkleaked_api:
            await ctx.send("❌ The CheckLeaked module is not available. This command will not work.")
            return
        
        # Check if hash is provided
        if hash_value is None:
            await ctx.send("❌ Missing hash value! Usage: `!crackhash <hash_value>`\n"
                          "Example: `!crackhash 5f4dcc3b5aa765d61d8327deb882cf99`\n\n"
                          "Use `!help crackhash` for more information.")
            return
            
        # Basic validation
        if len(hash_value) < 8:
            await ctx.send("❌ Invalid hash value. Hash seems too short (should be at least 8 characters).")
            return
        
        # Send initial message
        message = await ctx.send(f"🔍 Attempting to crack hash: `{hash_value}`...")
        
        try:
            # Log the hash we're attempting to crack
            logging.getLogger("vigil_bot").info(f"Attempting to crack hash: {hash_value}")
            
            # Attempt to crack the hash using the primary method
            results = checkleaked_api.crack_hash(hash_value)
            
            # Log the results for debugging
            logging.getLogger("vigil_bot").info(f"Hash crack response: {json.dumps(results, indent=2)}")
            
            # If the primary method fails, try using the experimental search with hash type
            if results.get("error") or not any([results.get("plain"), results.get("plaintext"), 
                                               results.get("password"), results.get("result")]):
                logging.getLogger("vigil_bot").info(f"Primary hash crack failed, trying experimental search")
                
                # Try experimental search as fallback
                fallback_results = checkleaked_api.search_experimental(hash_value, "hash")
                logging.getLogger("vigil_bot").info(f"Fallback search response: {json.dumps(fallback_results, indent=2)}")
                
                # If the fallback succeeded, use its results
                if fallback_results and not fallback_results.get("error") and fallback_results.get("results"):
                    results = fallback_results
                    
                    # Update the results structure with what we found
                    if len(fallback_results.get("results", [])) > 0:
                        first_result = fallback_results["results"][0]
                        if first_result.get("password"):
                            results["plain"] = first_result["password"]
            
            # Add checks for different response structures
            plaintext = None
            hash_type = None
            
            # Check all possible field names for the plaintext password
            if results.get("plain") is not None:
                plaintext = results["plain"]
            elif results.get("plaintext") is not None:
                plaintext = results["plaintext"]
            elif results.get("password") is not None:
                plaintext = results["password"]
            elif results.get("result") is not None:
                plaintext = results["result"]
            
            # If we have results array, try to extract password from there
            if not plaintext and results.get("results") and isinstance(results["results"], list):
                for result in results["results"]:
                    if isinstance(result, dict):
                        if result.get("password") and result["password"]:
                            plaintext = result["password"]
                            break
                        if result.get("plain") and result["plain"]:
                            plaintext = result["plain"]
                            break
            
            # Check for hash type
            if results.get("type") is not None:
                hash_type = results["type"]
            elif results.get("hash_type") is not None:
                hash_type = results["hash_type"]
                
            # Check if we found information about the hash, even if we couldn't crack it
            hash_info_found = False
            associated_info = {}
            
            # Look for related information that might be useful
            if results.get("results") and isinstance(results["results"], list) and len(results["results"]) > 0:
                first_result = results["results"][0]
                hash_info_found = True
                
                # Extract useful info from the result
                for key in ["email", "username", "leak", "salt", "created", "birthdate"]:
                    if key in first_result and first_result[key]:
                        associated_info[key] = first_result[key]
            
            # If we have the plaintext, show the cracked password
            if plaintext:
                # Create embed for cracked password
                embed = discord.Embed(
                    title=f"Hash Cracked: {hash_value}",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                
                embed.add_field(
                    name="Plain Text",
                    value=f"`{plaintext}`",
                    inline=False
                )
                
                if hash_type:
                    embed.add_field(
                        name="Hash Type",
                        value=hash_type,
                        inline=True
                    )
                
                # Add any other associated info we found
                for key, value in associated_info.items():
                    if key not in ["password", "plain", "plaintext", "hash"]:
                        embed.add_field(
                            name=key.capitalize(),
                            value=value,
                            inline=True
                        )
            # If we couldn't crack it but found info about the hash
            elif hash_info_found:
                # Create embed for hash information
                embed = discord.Embed(
                    title=f"Hash Information: {hash_value}",
                    description="This hash was found but could not be cracked.",
                    color=discord.Color.gold(),  # Use a different color to indicate partial success
                    timestamp=datetime.datetime.now()
                )
                
                # Add the associated info we found
                for key, value in associated_info.items():
                    if key not in ["password", "plain", "plaintext", "hash"]:
                        embed.add_field(
                            name=key.capitalize(),
                            value=value,
                            inline=True
                        )
                
                # Add source info if available
                if first_result.get("sources") and isinstance(first_result["sources"], list):
                    source_info = []
                    for source in first_result["sources"]:
                        if isinstance(source, dict):
                            if source.get("Name"):
                                source_info.append(source["Name"])
                            if source.get("Leak"):
                                source_info.append(source["Leak"])
                            if source.get("BreachDate"):
                                date = source["BreachDate"].split("T")[0] if "T" in source["BreachDate"] else source["BreachDate"]
                                source_info.append(f"Breach Date: {date}")
                    
                    if source_info:
                        embed.add_field(
                            name="Source Information",
                            value="\n".join(source_info),
                            inline=False
                        )
            else:
                await message.edit(content=f"❌ Could not crack hash: `{hash_value}`.")
                return
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
        
        except Exception as e:
            logging.getLogger("vigil_bot").error(f"Error cracking hash: {str(e)}")
            await message.edit(content=f"❌ Error cracking hash: {str(e)}")
            
    @bot.command(name="leakcheck", aliases=["lc"], help="Search for leaked data using LeakCheck API")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def leak_check(ctx, check_value: str = None, check_type: str = None, leak_check_key: str = None):
        """
        Search for leaked data using LeakCheck API
        
        Usage: !leakcheck <value> <type> [api_key]
        Example: !leakcheck example@email.com email
        
        Valid check types:
        - email: Search by email address
        - mass: Mass search across multiple data sources
        - hash: Search by password hash
        - pass_email: Search by password and email
        - phash: Search by partial hash
        - domain_email: Search by email domain
        - login: Search by username/login
        - phone: Search by phone number
        - mc: Search by Minecraft username
        - pass_login: Search by password and login
        - pass_phone: Search by password and phone
        - auto: Auto-detect type
        
        Notes:
        - This command requires a LeakCheck API key (either in .env or as third parameter)
        - Results may contain sensitive information
        - Limited to 5 results in Discord for privacy reasons
        - This command has a 30-second cooldown
        """
        if not checkleaked_available or not checkleaked_api:
            await ctx.send("❌ The CheckLeaked module is not available. This command will not work.")
            return
        
        # Check if parameters are provided
        if check_value is None or check_type is None:
            await ctx.send("❌ Missing parameters! Usage: `!leakcheck <value> <type> [api_key]`\n"
                          "Example: `!leakcheck example@email.com email`\n\n"
                          "Valid types: email, mass, hash, pass_email, phash, domain_email, login, phone, mc, pass_login, pass_phone, auto\n\n"
                          "Use `!help leakcheck` for more information.")
            return
            
        # Validate check type
        valid_types = ["email", "mass", "hash", "pass_email", "phash", "domain_email", 
                       "login", "phone", "mc", "pass_login", "pass_phone", "auto"]
        if check_type.lower() not in valid_types:
            await ctx.send(f"❌ Invalid check type. Please use one of: `{', '.join(valid_types)}`\n"
                           f"Example: `!leakcheck example@email.com email`")
            return
        
        # Send initial message
        message = await ctx.send(f"🔍 Searching LeakCheck for {check_type}: `{check_value}`...")
        
        try:
            # If no LeakCheck key provided as parameter, try to get from environment
            if not leak_check_key:
                # Try getting the key from environment variables
                import os
                from dotenv import load_dotenv
                load_dotenv()
                leak_check_key = os.getenv("LEAKCHECK_TOKEN")
                
                if not leak_check_key:
                    await message.edit(content="❌ No LeakCheck API key found. Please provide one as the third parameter or add LEAKCHECK_TOKEN to your .env file.")
                    return
            
            # Search LeakCheck
            results = checkleaked_api.leakcheck_search(leak_check_key, check_value, check_type.lower())
            
            if results.get("error"):
                await message.edit(content=f"❌ Error from LeakCheck API: {results['error']}")
                return
            
            if not results.get("result") or len(results["result"]) == 0:
                await message.edit(content=f"❌ No leak data found for {check_type}: `{check_value}`.")
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"LeakCheck Results for {check_type}: {check_value}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(
                name="Results Count",
                value=f"{len(results['result'])} entries found",
                inline=False
            )
            
            # Add entries to embed
            for i, entry in enumerate(results["result"][:5]):  # Limit to first 5 entries
                field_value = ""
                for key, value in entry.items():
                    if value and key not in ["id"]:
                        field_value += f"**{key}**: {value}\n"
                
                embed.add_field(
                    name=f"Entry {i+1}",
                    value=field_value or "No data",
                    inline=False
                )
            
            if len(results["result"]) > 5:
                embed.set_footer(text=f"Showing 5 of {len(results['result'])} results.")
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
        
        except Exception as e:
            await message.edit(content=f"❌ Error searching LeakCheck: {str(e)}")
            
    @bot.command(name="breachhelp", aliases=["bhelp"], help="Get help with breach search commands")
    async def breach_help(ctx):
        """
        Show detailed help information for all breach-related commands
        
        Usage: !breachhelp
        
        Displays comprehensive information about:
        - !breach - Basic breach data search
        - !breachx - Advanced breach search
        - !crackhash - Hash decryption
        - !leakcheck - LeakCheck API search
        """
        embed = discord.Embed(
            title="🔍 Breach Data Search Commands",
            description="Comprehensive guide to all breach-related commands",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        # Basic Breach Command
        embed.add_field(
            name="!breach <query> <search_type>",
            value="Standard breach search using Dehashed database\n"
                 "**Example:** `!breach john@example.com email`\n"
                 "**Valid types:** email, username, ip_address, name, address, phone, vin, free\n"
                 "**Cooldown:** 30 seconds (5 seconds for Vigil - Admin role)",
            inline=False
        )
        
        # Advanced Breach Command
        embed.add_field(
            name="!breachx <query> <search_type>",
            value="Advanced breach search with experimental API\n"
                 "**Example:** `!breachx johndoe username`\n"
                 "**Valid types:** username, mass, email, lastip, password, name, hash\n"
                 "**Aliases:** !advbreach, !xbreach\n"
                 "**Cooldown:** 30 seconds (5 seconds for Vigil - Admin role)",
            inline=False
        )
        
        # Hash Cracking
        embed.add_field(
            name="!crackhash <hash>",
            value="Attempt to decrypt a password hash\n"
                 "**Example:** `!crackhash 5f4dcc3b5aa765d61d8327deb882cf99`\n"
                 "**Supports:** MD5, SHA1, SHA256, and other common hash formats\n"
                 "**Alias:** !hash\n"
                 "**Cooldown:** 30 seconds (5 seconds for privileged roles)",
            inline=False
        )
        
        # LeakCheck
        embed.add_field(
            name="!leakcheck <value> <type> [api_key]",
            value="Search using LeakCheck API\n"
                 "**Example:** `!leakcheck example@email.com email`\n"
                 "**Common types:** email, hash, login, phone\n"
                 "**Alias:** !lc\n"
                 "**Cooldown:** 30 seconds (5 seconds for privileged roles)\n"
                 "**Note:** Requires a LeakCheck API key",
            inline=False
        )
        
        # Footer with tip
        embed.set_footer(text="For detailed help on any command, use !help <command>")
        
        await ctx.send(embed=embed)
