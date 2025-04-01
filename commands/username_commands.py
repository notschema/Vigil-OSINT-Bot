"""
Username search commands for Vigil OSINT Bot
"""

import json
import datetime
import sys
import aiohttp
import discord
from discord.ext import commands
from pathlib import Path
import logging
import os
import re
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger("vigil_bot")

from .utils import (
    execute_command, 
    get_python_executable, 
    whatsmyname_available, 
    masto_available, 
    socialscan_available, 
    toutatis_available,
    sherlock_available,
    TEMP_DIR
)

if whatsmyname_available:
    from WhatsMyName.whatsmyname_discord import check_username_existence

if masto_available:
    from Masto.masto import username_search, username_search_api, instance_search

def truncate_links(found_sites):
    """
    Process found sites, removing failed lookups and formatting successful ones
    
    Args:
        found_sites (list): List of (site_name, url) tuples
    
    Returns:
        list of tuples with successful sites
    """
    # Filter out sites with error messages and keep only valid URLs
    successful_sites = [
        (site, url) for site, url in found_sites 
        if url and not any(keyword in url.lower() for keyword in ['error', 'failed', 'denied'])
    ]
    
    return successful_sites

# Import dynamic cooldown from breach_commands
def register_username_commands(bot):
    # ... (previous existing commands remain unchanged)

    @bot.command(name="sherlock", help="Find username across social networks")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def sherlock_search(ctx, username: str = None):
        """
        Search for a username across social networks using Sherlock
        
        Usage: 
        !sherlock <username> - Search for username on social networks
        
        Notes:
        - Generates detailed reports with links to all found profiles
        - May take some time to complete depending on the number of sites
        """
        
        # Check if username is provided
        if username is None:
            await ctx.send("❌ Missing username! Usage: `!sherlock <username>`\nExample: `!sherlock johndoe`")
            return
        
        # Validate username
        if len(username) > 30:
            await ctx.send("❌ Username is too long. Please limit to 30 characters.")
            return
        
        # Check if sherlock is available
        if not sherlock_available:
            await ctx.send("❌ The Sherlock module is not properly installed or configured.")
            return
        
        # Send initial message
        message = await ctx.send(f"🔍 Searching for username `{username}` across social networks. This may take a minute...")
        
        # Create temp directory for output
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Prepare output file path
        result_file = temp_dir / f"{username}_sherlock.txt"
        
        try:
            # Manually run Sherlock with subprocess to ensure compatibility
            python_exe = get_python_executable()
            sherlock_dir = os.path.abspath("Sherlock")
            
            # Use the installed sherlock_project package with the correct module name
            result_file_abs = os.path.abspath(result_file)
            
            # Updated command with the correct module name
            cmd = (
                f"{python_exe} -m sherlock_project.sherlock {username} "
                f"--timeout 30 "  # Increased timeout for better results
                f"--print-found "  # Only print found results
                f"--output \"{result_file_abs}\" "  # Save results to file with absolute path
                f"--no-color"  # No color output for easier parsing
            )
            
            logger.info(f"Running Sherlock command: {cmd}")
            success, output = await execute_command(cmd, timeout=120)  # 2-minute timeout
            
            logger.info(f"Sherlock command output (first 500 chars): {output[:500]}")
            
            if not success:
                logger.error(f"Sherlock command failed: {output}")
                await message.edit(content=f"❌ Error running Sherlock: {output}")
                return
            
            # Parse the Sherlock results
            found_sites = []
            total_found = 0
            
            # For debugging
            logger.info(f"Command output sample: {output[:500]}")
            
            # Direct pattern match from command output (most reliable)
            import re
            # Match lines like "[+] SiteName: https://example.com/username"
            sherlock_pattern = re.compile(r'\[\+\]\s+(.*?):\s+(https?://\S+)')
            
            # Process command output
            matches = sherlock_pattern.findall(output)
            for site_name, url in matches:
                found_sites.append((site_name.strip(), url.strip()))
            
            # Count found sites
            total_found = len(found_sites)
            
            # Log the results
            logger.info(f"Found {total_found} sites from command output for username '{username}'")
            
            # Final check: if no results were found in the output but Sherlock ran successfully,
            # we'll manually search for lines that look like URLs
            if total_found == 0:
                # Look for URLs in the output
                url_pattern = re.compile(r'(https?://\S+)')
                url_matches = url_pattern.findall(output)
                
                for url in url_matches:
                    if url.startswith("http"):
                        try:
                            parsed_url = urlparse(url)
                            site_name = parsed_url.netloc.replace("www.", "")
                            found_sites.append((site_name, url))
                        except:
                            continue
                
                # Update count
                total_found = len(found_sites)
                if total_found > 0:
                    logger.info(f"Found {total_found} sites by URL parsing in output")
            
            # Try to read from the output file as a last resort
            if total_found == 0 and result_file.exists():
                try:
                    with open(result_file, "r", encoding="utf-8") as file:
                        file_content = file.read()
                        logger.info(f"Result file exists with {len(file_content)} bytes")
                        
                        # Check for URLs in the file
                        url_pattern = re.compile(r'(https?://\S+)')
                        url_matches = url_pattern.findall(file_content)
                        
                        file_sites = []
                        for url in url_matches:
                            try:
                                parsed_url = urlparse(url)
                                site_name = parsed_url.netloc.replace("www.", "")
                                file_sites.append((site_name, url))
                            except:
                                continue
                        
                        if file_sites:
                            found_sites = file_sites
                            total_found = len(file_sites)
                            logger.info(f"Found {total_found} sites from result file")
                except Exception as e:
                    logger.error(f"Error reading result file: {e}")
            
            # Final detection - can we manually find sites in the output?
            if total_found == 0:
                # Desperate mode: try to look for known social media domains in the output
                known_domains = [
                    "facebook.com", "twitter.com", "instagram.com", "github.com", 
                    "reddit.com", "youtube.com", "linkedin.com", "pinterest.com",
                    "tiktok.com", "tumblr.com", "medium.com", "quora.com",
                    "soundcloud.com", "spotify.com", "discord.com", "twitch.tv"
                ]
                
                for domain in known_domains:
                    if domain in output:
                        # Try to extract a URL containing this domain
                        domain_pattern = re.compile(f'(https?://[^\\s]*{domain}[^\\s]*)')
                        domain_matches = domain_pattern.findall(output)
                        
                        for url in domain_matches:
                            found_sites.append((domain.replace(".com", ""), url))
                
                # Update count again
                total_found = len(found_sites)
                if total_found > 0:
                    logger.info(f"Found {total_found} sites by domain search in output")
            
            # Final log based on results
            if total_found == 0:
                logger.warning(f"No results found for username '{username}' after all parsing attempts")
            else:
                logger.info(f"Successfully found {total_found} results for username '{username}'")
                logger.info(f"First few results: {found_sites[:3]}")
            
            # Create embed with results
            embed = discord.Embed(
                title=f"Sherlock Results for {username}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            
            embed.description = f"**Found {total_found} account(s) across social networks**"
            
            # Add fields with chunked results (Discord has a limit on field length)
            chunks = [found_sites[i:i+10] for i in range(0, len(found_sites), 10)]
            
            for i, chunk in enumerate(chunks[:10]):  # Limit to 10 fields (100 results max)
                field_value = "\n".join([f"[{site_name}]({url})" for site_name, url in chunk])
                if not field_value:
                    field_value = "No accounts found in this batch."
                
                embed.add_field(
                    name=f"Accounts {i*10+1}-{i*10+len(chunk)}",
                    value=field_value,
                    inline=False
                )
            
            if len(found_sites) > 100:
                embed.set_footer(text=f"Showing 100 of {total_found} total accounts found.")
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
            
            # If no accounts found, provide a message
            if total_found == 0:
                await message.edit(content=f"🔎 No accounts found for username `{username}`.")
        
        except Exception as e:
            logger.error(f"Error processing Sherlock results: {str(e)}")
            await message.edit(content=f"❌ Error processing Sherlock results: {str(e)}")
        
        finally:
            # Clean up the result file
            try:
                if result_file.exists():
                    result_file.unlink()
            except Exception:
                pass
    
    @bot.command(name="maigret", help="Comprehensive username search across websites")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def maigret_search(ctx, username: str = None, full_search: bool = False):
        """
        Perform a comprehensive username search across websites
        
        Usage: 
        !maigret <username> - Search top 50 sites
        !maigret <username> -a - Search ALL sites

        Notes:
        - Standard search covers the top 50 most popular sites
        - Comprehensive mode (-a) searches all known sites
        - Takes 2-4 minutes to complete
        - Generates detailed report with all findings
        """
        
        # Check if username is provided
        if username is None:
            await ctx.send("❌ Missing username! Usage: `!maigret <username>` or `!maigret <username> -a`\nExample: `!maigret johndoe`")
            return
        
        # Check for full search flag
        if username == '-a':
            full_search = True
            username = ctx.args[2] if len(ctx.args) > 2 else None
        
        # Validate username
        if not username:
            await ctx.send("❌ Missing username! Usage: `!maigret <username>` or `!maigret <username> -a`\nExample: `!maigret johndoe`")
            return
        
        # Check if maigret is available
        if not getattr(sys.modules.get('commands.utils'), 'maigret_available', False):
            await ctx.send("❌ The Maigret module is not properly installed or configured.")
            return
            
        # Limit username length
        if len(username) > 30:
            await ctx.send("❌ Username is too long. Please limit to 30 characters.")
            return
        
        # Send initial message
        search_type = "all sites" if full_search else "top 50 sites"
        message = await ctx.send(f"🔍 Searching for username `{username}` across {search_type}. This may take several minutes...")
        
        # Create temp directory for output
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Create a results directory specific to this run
        results_folder = temp_dir / f"{username}_results"
        results_folder.mkdir(exist_ok=True)
        
        # Prepare Maigret command with more reliable direct paths
        python_exe = get_python_executable()
        abs_results_folder = os.path.abspath(results_folder)
        
        # Create an initial file to flag the command started
        flag_file = results_folder / "command_started.txt"
        with open(flag_file, "w") as f:
            f.write(f"Command started at {datetime.datetime.now()}")
        
        # Run Maigret with full site coverage for better results
        cmd = (
            f"{python_exe} -m maigret {username} "
            f"--folderoutput \"{abs_results_folder}\" "
            "--no-recursion "        # Don't search recursively
            "--no-extracting "       # Skip extracting additional info
            "--timeout 15 "          # Slightly longer timeout per site
            "--retries 2 "           # Two retries for better results
            "--max-connections 10 "  # More connections for faster completion
            "--no-color "            # No color output
            "--no-progressbar "      # No progress bars
            "--verbose "             # Verbose output
            "-P "                    # Generate PDF report
        )
        
        # Add site search scope - use more sites for better coverage
        if full_search:
            cmd += "-a "             # Full site coverage for comprehensive search
        else:
            cmd += "--top-sites 50 " # Search top 50 sites by default
        
        maigret_output = ""
        try:
            # Tell the user the command is running
            await message.edit(content=f"🔍 Searching for username `{username}` across {'all' if full_search else 'top 50'} sites. This will take a few minutes...")
            
            # Run with a longer timeout for more comprehensive results
            success, maigret_output = await execute_command(cmd, timeout=180)  # 3-minute timeout
            
            # Check if the output contains usage help (which means the command had errors)
            if maigret_output.startswith("usage:"):
                logger.error("Maigret command returned help text instead of results")
                
                # Try a more basic version as fallback
                simple_cmd = f"{python_exe} -m maigret {username}"
                logger.info(f"Trying simplified command: {simple_cmd}")
                success, maigret_output = await execute_command(simple_cmd, timeout=60)
                
                if maigret_output.startswith("usage:"):
                    await message.edit(content=f"❌ Error running Maigret for username `{username}`. The command could not be executed properly.")
                    return
            
            # Create a completion flag file
            flag_file = results_folder / "command_completed.txt"
            with open(flag_file, "w") as f:
                f.write(f"Command completed at {datetime.datetime.now()}\n")
                f.write(f"Output length: {len(maigret_output)} bytes\n")
                f.write(f"First 1000 chars: {maigret_output[:1000]}")
            
            # Log partial output for debugging (not the full output which could be huge)
            logger.info(f"Maigret command output (first 500 chars): {maigret_output[:500]}")
            
            if not success:
                logger.error(f"Maigret command failed: {maigret_output}")
                await message.edit(content=f"❌ Error running Maigret: {maigret_output}")
                return
        except Exception as e:
            logger.error(f"Exception when executing Maigret: {str(e)}")
            await message.edit(content=f"❌ Error running Maigret: {str(e)}")
            return
        
        try:
            # Find report files
            pdf_files = list(results_folder.glob("*report*.pdf"))
            
            # Use a simpler and more robust approach to extract results
            # First look for any mentions of websites in the output
            found_sites = []
            
            # More comprehensive pattern to extract site names and URLs
            # This matches [+] SiteName: http://example.com format
            site_pattern = re.compile(r'\[\+\]\s+([^:]+?):\s+(https?://\S+)')
            
            # Match positive results in the command output
            for site, url in site_pattern.findall(maigret_output):
                site_name = site.split('[')[0].strip() if '[' in site else site.strip()
                if url and url.strip() != '':
                    found_sites.append((site_name, url.strip()))
            
            # If we didn't find any with [+], try a more general pattern
            if not found_sites:
                general_pattern = re.compile(r'\[[^\]]*\]\s+([^:]+?):\s+(https?://\S+)')
                for site, url in general_pattern.findall(maigret_output):
                    site_name = site.split('[')[0].strip() if '[' in site else site.strip()
                    if url and url.strip() != '':
                        found_sites.append((site_name, url.strip()))
            
            # If no matches in output, look for any URLs
            if not found_sites:
                url_pattern = re.compile(r'(https?://\S+)')
                for url in url_pattern.findall(maigret_output):
                    if url and url.strip() != '':
                        try:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url.strip())
                            site_name = parsed_url.netloc.replace("www.", "")
                            found_sites.append((site_name, url.strip()))
                        except:
                            continue
            
            # Check the results directory for any generated files
            # Maigret generates several useful files we can use
            
            # Check for textual report first (most reliable)
            txt_report = list(results_folder.glob("*report.txt"))
            if txt_report:
                try:
                    with open(txt_report[0], "r", encoding="utf-8", errors="replace") as f:
                        report_content = f.read()
                        
                        # Extract sites from the report
                        site_pattern = re.compile(r'(?:^|\n)(\w+.*?):\s+(https?://\S+)', re.MULTILINE)
                        for site_name, url in site_pattern.findall(report_content):
                            if url and url.strip() != '':
                                found_sites.append((site_name.strip(), url.strip()))
                except Exception as e:
                    logger.error(f"Error reading text report: {e}")
            
            # Also check JSON report which may contain more structured data
            json_report = list(results_folder.glob("*.json"))
            if json_report:
                try:
                    with open(json_report[0], "r", encoding="utf-8", errors="replace") as f:
                        import json
                        try:
                            json_data = json.load(f)
                            # Extract from typical Maigret JSON structure
                            if isinstance(json_data, dict) and "results" in json_data:
                                for site_name, site_data in json_data["results"].items():
                                    if isinstance(site_data, dict) and "url_user" in site_data:
                                        url = site_data["url_user"]
                                        if url and "http" in url:
                                            found_sites.append((site_name, url))
                        except json.JSONDecodeError:
                            # If not valid JSON, just look for URLs
                            content = f.read()
                            url_pattern = re.compile(r'(https?://\S+)')
                            for url in url_pattern.findall(content):
                                if url and url.strip() != '':
                                    try:
                                        parsed_url = urlparse(url.strip())
                                        site_name = parsed_url.netloc.replace("www.", "")
                                        found_sites.append((site_name, url.strip()))
                                    except:
                                        continue
                except Exception as e:
                    logger.error(f"Error reading JSON report: {e}")
            
            # As a last resort, check any other files in the directory
            if not found_sites:
                all_files = list(results_folder.glob("*.*"))
                
                for file_path in all_files:
                    # Skip binary files and already processed ones
                    if file_path.suffix.lower() in ['.pdf', '.png', '.jpg']:
                        continue
                        
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                            
                            # Look for URLs in the file
                            url_pattern = re.compile(r'(https?://\S+)')
                            for url in url_pattern.findall(content):
                                if url and url.strip() != '':
                                    try:
                                        parsed_url = urlparse(url.strip())
                                        site_name = parsed_url.netloc.replace("www.", "")
                                        found_sites.append((site_name, url.strip()))
                                    except:
                                        continue
                    except:
                        continue
            
            # Process and filter the found sites
            successful_sites = truncate_links(found_sites)
            total_accounts = len(successful_sites)
            
            # Use simpler approch for getting stats
            countries = []
            interests = []
            error_stats = {}
            
            # Look for countries and interests in the output
            countries_match = re.search(r'Countries:\s+(.+?)(\s|\n)', maigret_output)
            if countries_match:
                countries = [c.strip() for c in countries_match.group(1).split(',') if c.strip()]
                
            interests_match = re.search(r'Interests \(tags\):\s+(.+?)(\s|\n)', maigret_output)
            if interests_match:
                interests = [i.strip() for i in interests_match.group(1).split(',') if i.strip()]
            
            # Create embed with detailed information
            embed = discord.Embed(
                title=f"Maigret Results for {username}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now()
            )
            
            # Detailed stats with error information
            error_details = " | ".join([f"{k}: {v}%" for k, v in error_stats.items()]) if error_stats else "None"
            
            embed.description = (
                f"**Total Accounts Found:** {total_accounts}\n"
                f"**Unique Links:** {len(successful_sites)}\n"
                f"**Countries Detected:** {', '.join(countries) or 'None'}\n"
                f"**Interests/Tags:** {', '.join(interests) or 'None'}\n"
                f"**Search Scope:** {'All Sites' if full_search else 'Top 50 Sites'}\n\n"
                f"**Error Statistics:** {error_details}"
            )
            
            # Add fields with successful sites
            chunks = [successful_sites[i:i+10] for i in range(0, len(successful_sites), 10)]
            
            for i, chunk in enumerate(chunks[:5]):  # Limit to 5 fields
                field_value = "\n".join([f"[{site_name}]({url})" for site_name, url in chunk])
                embed.add_field(
                    name=f"Accounts {i*10+1}-{i*10+len(chunk)}",
                    value=field_value,
                    inline=False
                )
            
            if len(successful_sites) > 50:
                embed.set_footer(text=f"Showing 50 of {len(successful_sites)} total accounts found.")
            
            # Measure embed length
            embed_length = len(embed.description) + sum(len(field.name) + len(field.value) for field in embed.fields)
            
            # Send PDF privately only if embed is too long
            discord_files = [discord.File(file) for file in pdf_files]
            
            if embed_length > 5500:  # If embed is too long
                # Send detailed PDF privately
                await ctx.author.send(
                    "📄 The full Maigret report was too large to display in the channel. Here's the PDF:", 
                    files=discord_files
                )
                
                # Truncate the embed for public view
                embed.description = (
                    f"**Total Accounts Found:** {total_accounts}\n"
                    f"📄 Full report sent via private message."
                )
                embed.clear_fields()
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
        
        except Exception as e:
            logger.error(f"Error processing Maigret results: {str(e)}")
            await message.edit(content=f"❌ Error processing Maigret results: {str(e)}")
        
        finally:
            # Clean up temp files after a delay to ensure upload
            import asyncio
            await asyncio.sleep(5)
            try:
                import shutil
                results_folder = temp_dir / f"{username}_results"
                if results_folder.exists():
                    shutil.rmtree(results_folder)
            except Exception:
                pass
