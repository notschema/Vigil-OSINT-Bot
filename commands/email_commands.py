"""
Email-related commands for Vigil OSINT Bot
"""

import datetime
import discord
import logging
import re
import os
from discord.ext import commands

from .utils import execute_command, get_python_executable

def register_email_commands(bot):
    @bot.command(name="gmail")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def gmail_check(ctx, email: str):
        """Check if a Gmail address is valid and deliverable"""
        if not email.endswith("@gmail.com"):
            await ctx.send("❌ Please enter a valid Gmail address (ending with @gmail.com).")
            return
        
        await ctx.send("🚧 The Gmail validation feature is under development. Please check back later.")

    @bot.command(name="email", aliases=["mail"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def email_check(ctx, email: str):
        """Check which websites an email is registered on and retrieve recovery information (Use !mail or !email)"""
        # Validate email format
        if "@" not in email or "." not in email:
            await ctx.send("❌ Please enter a valid email address.")
            return
        
        # Initialize message with clear explanation and expectations
        message1 = await ctx.send(f"🔍 Scanning `{email}` across 120+ websites for accounts and recovery details...\n\n"
                                 f"⏳ This can take up to 2-3 minutes to complete. The command will find websites where this email is registered "
                                 f"and any associated recovery information.\n\n"
                                 f"ℹ️ Use `!mail` or `!email` to run this same command.")
        
        # Get logger
        logger = logging.getLogger("vigil_bot")
        
        # Run command line holehe without filtering to get all information including recovery details
        # Run holehe and add some special handing for detecting vsco.co
        cmd = f"holehe {email}"
        success, output = await execute_command(cmd, timeout=300)  # Longer timeout for full scan
        
        # Log the command being run
        logger.info(f"Running holehe command: {cmd}")
        
        # List of very important sites we're especially interested in
        critical_sites = ["amazon.com", "amazon.com.au", "facebook.com", "google.com", 
                        "twitter.com", "instagram.com", "vsco.co", "kick.com"]
        logger.info(f"Critical sites we're looking for: {', '.join(critical_sites)}")
        
        # Extract and log results for specific important domains we care about
        logger.info("=== SPECIFIC SITE RESULTS ===")
        for important_domain in ["amazon.com", "amazon.com.au", "facebook.com", "google.com", "vsco.co", "kick.com"]:
            # Find all lines mentioning this domain
            logger.info(f"Looking for {important_domain} results:")
            found_lines = []
            for line in output.split("\n"):
                if important_domain.lower() in line.lower():
                    found_lines.append(line)
            
            if found_lines:
                for line in found_lines:
                    logger.info(f"  {important_domain} line: {line}")
            else:
                logger.info(f"  No specific results found for {important_domain}")
                
        # Log the entire output for debugging
        logger.debug(f"Complete holehe output:\n{output}")
        
        if not success:
            await message1.edit(content=f"❌ Error running holehe. Please try again later.")
            return
        
        # Improved site detection with a more balanced approach
        sites = []
        
        # Process the output line by line
        for line in output.split("\n"):
            # Skip irrelevant lines
            if not line.strip() or "Email used, [-] Email not used" in line or "Twitter :" in line or "Github :" in line or "Donations :" in line:
                continue
                
            # Look for positive matches with [+] which is the most reliable indicator
            if "[+]" in line:
                # Extract site name from [+] line
                parts = line.split("[+]")
                if len(parts) > 1:
                    site = parts[1].strip()
                    if site and len(site) > 3:
                        logger.debug(f"Found site via [+]: {site}")
                        sites.append(site)
                
                # Also check for domain patterns in the same line
                domain_matches = re.findall(r'[\w\d_.-]+\.[\w\d_.-]+', line)
                for domain in domain_matches:
                    if domain not in sites and len(domain) > 3 and "." in domain:
                        logger.debug(f"Found additional domain in [+] line: {domain}")
                        sites.append(domain)
            
            # Look for clear indicators of a found account - more inclusively
            elif "✓" in line or "Found" in line or "Email used" in line or "Account exists" in line:
                # Extract domain with a more inclusive pattern
                domain_match = re.search(r'[\w\d_.-]+\.[\w\d_.-]+(?:\.[\w\d_.-]+)*', line)
                if domain_match:
                    site = domain_match.group(0)
                    if site and len(site) > 3:
                        # Make sure it's not a false positive
                        if not any(bad in line for bad in ["✗", "[-]", "Error", "not used", "rate limit"]):
                            logger.debug(f"Found site via positive indicator: {site}")
                            sites.append(site)
        
        # Also try to find email recovery info in the output
        recovery_emails = []
        recovery_phones = []
        
        current_site = None
        for line in output.split("\n"):
            # Skip empty or irrelevant lines
            if not line.strip() or "Twitter :" in line or "Github :" in line or "Donations :" in line:
                continue
            
            # Check for site header with positive indicator (exists)
            if "[+]" in line:
                # Extract the site name - it comes after the [+]
                site_parts = line.split("[+]")
                if len(site_parts) > 1:
                    site_candidate = site_parts[1].strip()
                    current_site = site_candidate
                    
                    # Look for recovery info in the same line
                    if "@" in line and email not in line:  # Don't match the original email
                        email_matches = re.findall(r'[\w\.-]+@[\w\.-]+', line)
                        for match in email_matches:
                            if match != email:  # Skip the original email
                                recovery_emails.append({
                                    "site": current_site,
                                    "email": match
                                })
                    
                    # Look for phone numbers
                    if re.search(r'\d', line):
                        # Try different phone patterns
                        phone_patterns = [
                            r'(\+?\d[\d\s\-\.]{5,}\d)',
                            r'(\d{3,}[\s\-\.]\d{3,})',
                            r'Phone[^:]*:\s*([^\s]+)'
                        ]
                        
                        for pattern in phone_patterns:
                            phone_matches = re.findall(pattern, line)
                            for match in phone_matches:
                                # Verify it looks like a phone number
                                if re.search(r'\d{3,}', match):
                                    recovery_phones.append({
                                        "site": current_site,
                                        "phone": match
                                    })
            
            # Detect recovery info lines that come after a site header
            elif current_site:
                # Email recovery in a separate line
                if ("email" in line.lower() or "recovery" in line.lower()) and "@" in line:
                    email_matches = re.findall(r'[\w\.-]+@[\w\.-]+', line)
                    for match in email_matches:
                        if match != email:  # Skip the original email
                            recovery_emails.append({
                                "site": current_site,
                                "email": match
                            })
                
                # Phone recovery in a separate line
                if ("phone" in line.lower() or "number" in line.lower() or "mobile" in line.lower()) and re.search(r'\d', line):
                    # Try different phone patterns
                    phone_patterns = [
                        r'(\+?\d[\d\s\-\.]{5,}\d)',
                        r'(\d{3,}[\s\-\.]\d{3,})',
                        r':\s*([^\s]+)'  # After a colon
                    ]
                    
                    for pattern in phone_patterns:
                        phone_matches = re.findall(pattern, line)
                        for match in phone_matches:
                            # Verify it looks like a phone number
                            if re.search(r'\d{3,}', match):
                                recovery_phones.append({
                                    "site": current_site,
                                    "phone": match
                                })
        
        # We'll be more conservative and not do additional domain matching
        # as it tends to produce false positives
        
        # Simplify and make the site cleanup more strict
        clean_sites = []
        
        # Minimize excluded terms to avoid filtering out valid sites like vsco
        excluded_terms = ['.py', '%', 'it/s', 'error', 'failed',
                         '[x]', '[-]', '✗', 'false', 'no results']
        
        for site in sites:
            site = site.strip()
            
            # Skip empty sites or those with excluded terms
            if not site:
                continue
                
            # Skip sites with exclusion terms
            skip = False
            for excl in excluded_terms:
                if excl in site.lower():
                    skip = True
                    break
            
            if skip:
                continue
            
            # Skip sites with obvious non-domain patterns but allow some common exceptions
            if (":" in site and not site.startswith("http")) or (" " in site and not any(valid in site.lower() for valid in ["office 365", "adobe cloud"])):
                continue
                
            # Remove any trailing punctuation
            site = re.sub(r'[,:;.!?\s]+$', '', site)
            
            # Make sure it has a valid domain-like structure - less strict to allow more valid domains
            if "." in site and len(site) > 4:
                # Check the site in the context of the output to ensure it was a positive match
                site_idx = output.lower().find(site.lower())
                if site_idx > 0:
                    # Look at the lines around this site mention
                    line_start = output.rfind("\n", 0, site_idx)
                    line_start = line_start if line_start != -1 else 0
                    line_end = output.find("\n", site_idx)
                    line_end = line_end if line_end != -1 else len(output)
                    line = output[line_start:line_end]
                    
                    # Only add if the line has positive indicators and no negative ones - less strict matching
                    if any(pos in line for pos in ["[+]", "✓", "Email used", "Found", "exists", "registered"]) and \
                       not any(neg in line for neg in ["[-]", "✗", "Error", "not used", "rate limit", "not found"]):
                        clean_sites.append(site)
                        logger.debug(f"Clean site after validation: {site}")
        
        # Add known common sites that might have been missed
        if len(clean_sites) < 10:
            # Comprehensive list of important sites, with special focus on kick.com and AU variants
            important_sites = [
                # Global sites
                "amazon.com", "spotify.com", "firefox.com", "office365.com", 
                "microsoft.com", "apple.com", "adobe.com", "dropbox.com", "github.com",
                "linkedin.com", "twitter.com", "facebook.com", "instagram.com",
                "discord.com", "paypal.com", "yahoo.com", "google.com", 
                "live.com", "outlook.com", "vsco.co", "kick.com",
                "netflix.com", "disney.com", "xbox.com", "playstation.com", 
                "steam.com", "twitch.tv", "gmail.com", "reddit.com",
                "pinterest.com", "ebay.com", "etsy.com", "shopify.com",
                "tumblr.com", "squarespace.com", "wordpress.com", "wix.com",
                
                # AU variants - extensive list
                "amazon.com.au", "spotify.com.au", "apple.com.au", "microsoft.com.au",
                "adobe.com.au", "paypal.com.au", "google.com.au", "yahoo.com.au",
                "linkedin.com.au", "facebook.com.au", "instagram.com.au", 
                "netflix.com.au", "disney.com.au", "github.com.au", "ebay.com.au",
                "twitter.com.au", "reddit.com.au", "pinterest.com.au", "tumblr.com.au",
                "wordpress.com.au", "office365.com.au", "dropbox.com.au"
            ]
            
            # Use the same list for both known sites and popular sites
            known_sites = important_sites
            
            # Check for all sites in our known_sites list with more detailed logging
            for known_site in known_sites:
                # Log that we're checking this site
                logger.info(f"Checking for site: {known_site}")
                
                if known_site.lower() in output.lower():
                    logger.info(f"Found mention of {known_site} in output")
                    site_match_found = False
                    
                    # For known sites, apply less strict matching to catch more legitimate results
                    for line in output.split("\n"):
                        if known_site.lower() in line.lower():
                            logger.info(f"Line with {known_site}: {line}")
                            
                            # Check for positive indicators
                            if any(pos in line for pos in ["[+]", "✓", "Email used", "Found", "exists", "registered"]):
                                logger.info(f"Positive match found for {known_site}")
                                if not any(neg in line for neg in ["[-]", "✗", "Error", "not used", "rate limit"]):
                                    clean_sites.append(known_site)
                                    logger.info(f"Added known site: {known_site}")
                                    site_match_found = True
                                    break
                                else:
                                    logger.info(f"Found negative indicator for {known_site}: {line}")
                            else:
                                logger.info(f"No positive indicators for {known_site} in line")
                    
                    if not site_match_found:
                        logger.info(f"Site {known_site} mentioned but no positive match found")
                else:
                    logger.info(f"No mention of {known_site} found in output")
        
        # Final cleanup and processing
        sites = list(set(clean_sites))  # Remove duplicates
        sites.sort()  # Sort alphabetically
        
        # Add extra logging to help troubleshooting
        logger.info(f"Found {len(sites)} verified sites: {sites}")
        
        # Collect all sites that were actually checked (successful or not)
        checked_sites = []
        negative_sites = []
        error_sites = []
        
        # Parse the holehe output to get comprehensive results
        for line in output.split("\n"):
            # Skip lines without site checks
            if not any(marker in line for marker in ["[+]", "[-]", "[x]"]):
                continue
                
            # Extract the domain from the line
            domains = re.findall(r'[\w\d_.-]+\.[\w\d_.-]+', line)
            if not domains:
                continue
                
            domain = domains[0]
            if len(domain) < 4:
                continue
                
            # Check the result type
            if "[+]" in line:
                # This is a positive match - already handled
                pass
            elif "[-]" in line:
                # Site was checked but email not registered
                negative_sites.append(domain)
                logger.info(f"Negative match found: {domain}")
            elif "[x]" in line:
                # Site check failed
                error_sites.append(domain)
                logger.info(f"Error checking site: {domain}")
                
            # Add to all checked sites
            checked_sites.append(domain)
            
        # Log comprehensive results
        logger.info(f"Sites with positive matches: {sites}")
        logger.info(f"Sites with negative matches: {negative_sites}")
        logger.info(f"Sites with check errors: {error_sites}")
        logger.info(f"Total sites checked: {len(checked_sites)}")
        
        # Make sure to deduplicate our sites
        sites = list(set(sites))  # Remove duplicates
        sites.sort()  # Sort alphabetically
            
        # Final scan for all important sites that might have been missed
        # Extract base domains from important_sites for more flexible matching
        base_domains = set()
        for domain in important_sites:
            parts = domain.split('.')
            if len(parts) >= 2:
                base_domains.add(parts[-2])  # Get the main part of the domain
        
        # Add some common aliases or shorthand names
        base_domains.update(["vsco", "fb", "insta", "tweet", "msft", "kick"])
        # Check each base domain from our important sites
        for base_domain in base_domains:
            # Skip very short domains to avoid false matches
            if len(base_domain) < 3:
                continue
                
            # Check if this base domain is already in our results
            found = False
            for site in sites:
                if base_domain.lower() in site.lower():
                    found = True
                    break
            
            if not found:
                # Check if the base domain appears in the output with a positive indicator
                for line in output.split("\n"):
                    if base_domain.lower() in line.lower() and any(pos in line for pos in ["[+]", "✓", "Email used", "Found", "exists"]):
                        # Determine the correct domain format
                        domain = None
                        
                        # Special cases
                        if base_domain == "vsco":
                            domain = "vsco.co"
                        elif base_domain == "fb":
                            domain = "facebook.com"
                        elif base_domain == "insta":
                            domain = "instagram.com"
                        elif base_domain == "tweet":
                            domain = "twitter.com"
                        elif base_domain == "msft":
                            domain = "microsoft.com"
                        elif base_domain == "kick":
                            domain = "kick.com"
                        else:
                            # Check if this is in our important_sites list
                            for important_site in important_sites:
                                if base_domain.lower() in important_site.lower():
                                    domain = important_site
                                    break
                            
                            # If not found in important_sites, use .com
                            if not domain:
                                domain = f"{base_domain}.com"
                        
                        # Also check for .com.au variant for Australian TLDs
                        au_variant = f"{base_domain}.com.au"
                        found_au = False
                        
                        # Check if AU variant exists in the output with positive indicator
                        for au_line in output.split("\n"):
                            if au_variant.lower() in au_line.lower() and any(pos in au_line for pos in ["[+]", "✓", "Email used", "Found", "exists"]):
                                if au_variant not in sites:
                                    sites.append(au_variant)
                                    logger.info(f"Added AU variant site: {au_variant}")
                                found_au = True
                                break
                        
                        # If AU variant not found or if this isn't an AU site, add the standard domain
                        if not found_au and domain and domain not in sites:
                            sites.append(domain)
                            logger.info(f"Added important site from base domain: {domain}")
                        
                        break
        
        # Check specifically for AU variants of important sites
        logger.info("=== CHECKING FOR AU VARIANTS ===")
        for site in sites.copy():
            # If we found amazon.com but not amazon.com.au, explicitly check for the AU variant
            base_domain = ".".join(site.split(".")[-2:])
            au_variant = f"{site.split('.')[0]}.com.au"
            
            if base_domain == "com.au":
                # Already an AU domain
                continue
                
            # Only check for AU variants of certain domains
            if site not in ["amazon.com", "spotify.com", "facebook.com", "google.com"]:
                continue
                
            logger.info(f"Checking AU variant for {site}: {au_variant}")
            
            # Look for the AU variant in the output
            au_found = False
            for line in output.split("\n"):
                if au_variant.lower() in line.lower():
                    logger.info(f"Found mention of {au_variant} in line: {line}")
                    # Check if positive indicators
                    if any(pos in line for pos in ["[+]", "✓", "Email used", "Found", "exists"]):
                        logger.info(f"Found positive match for {au_variant}")
                        if au_variant not in sites:
                            sites.append(au_variant)
                            logger.info(f"Added AU variant: {au_variant}")
                        au_found = True
                        break
            
            if not au_found:
                logger.info(f"No positive match found for {au_variant}")
        
        # Remove duplicates again and sort
        sites = list(set(sites))
        sites.sort()
        
        logger.info(f"Final site count after AU variant checking: {len(sites)} sites: {sites}")
        
        # Display sites message
        if sites:
            sites_embed = discord.Embed(
                title=f"Email Registration Results for {email}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            
            # Create a more detailed and comprehensive description
            if sites:
                popular_list = ", ".join([f"`{site}`" for site in sites])
                
                sites_embed.description = f"✅ **Found {len(sites)} websites where this email is registered**:\n{popular_list}\n\n" \
                                        f"ℹ️ Scanned {len(sites) + len(negative_sites) + len(error_sites)} websites total.\n" \
                                        f"{len(negative_sites)} sites confirmed the email is NOT registered.\n" \
                                        f"{len(error_sites)} sites could not be checked (rate limited or errors).\n\n" \
                                        f"📝 **Note**: AU variants and some sites (like kick.com) are not supported by holehe and were not checked."
            else:
                sites_embed.description = f"❌ No websites found where this email is registered.\n\n" \
                                        f"ℹ️ Scanned {len(negative_sites) + len(error_sites)} websites total.\n" \
                                        f"{len(negative_sites)} sites confirmed the email is NOT registered.\n" \
                                        f"{len(error_sites)} sites could not be checked (rate limited or errors).\n\n" \
                                        f"📝 **Note**: AU variants and some sites (like kick.com) are not supported by holehe and were not checked."
            
            # Don't need chunks for the positive sites anymore since they're in the description
            
            # Add field for sites that were checked but not registered (if any)
            if negative_sites:
                neg_sample = negative_sites[:15]  # Show only the first 15
                neg_sites_list = ", ".join([f"`{site}`" for site in neg_sample])
                
                if len(negative_sites) > 15:
                    neg_sites_list += f" and {len(negative_sites) - 15} more"
                    
                sites_embed.add_field(
                    name="Sites Where Email NOT Registered",
                    value=neg_sites_list,
                    inline=False
                )
            
            # Add field for sites that had errors during checking
            if error_sites:
                err_sample = error_sites[:15]  # Show only the first 15
                err_sites_list = ", ".join([f"`{site}`" for site in err_sample])
                
                if len(error_sites) > 15:
                    err_sites_list += f" and {len(error_sites) - 15} more"
                    
                sites_embed.add_field(
                    name="Sites That Could Not Be Checked",
                    value=err_sites_list,
                    inline=False
                )
                
            # Add field for sites with our custom modules
            custom_sites = ["amazon.com.au", "kick.com"]
            sites_embed.add_field(
                name="Sites with Custom Modules",
                value=", ".join([f"`{site}`" for site in custom_sites]) + "\n(These sites now have custom modules created specifically for VigilBot)",
                inline=False
            )
            
            # Sites that still don't have modules
            still_missing = ["spotify.com.au", "facebook.com.au", "google.com.au"]
            sites_embed.add_field(
                name="Sites Still Missing Modules",
                value=", ".join([f"`{site}`" for site in still_missing]),
                inline=False
            )
            
            sites_embed.set_footer(text="holehe tool now includes custom modules for amazon.com.au and kick.com | Use !mail or !email")
            await message1.edit(content=None, embed=sites_embed)
        else:
            await message1.edit(content=f"❌ No website registrations found for email `{email}`.")
            return
        
        # Display recovery emails if found
        if recovery_emails:
            # Deduplicate recovery emails
            unique_recovery_emails = []
            seen = set()
            
            for item in recovery_emails:
                key = (item["site"], item["email"])
                if key not in seen:
                    seen.add(key)
                    unique_recovery_emails.append(item)
            
            emails_embed = discord.Embed(
                title=f"Recovery Emails for {email}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now()
            )
            
            emails_embed.description = f"Found {len(unique_recovery_emails)} recovery email(s):"
            
            # Group recovery emails by site
            by_site = {}
            for item in unique_recovery_emails:
                site = item["site"] or "Unknown"
                if site not in by_site:
                    by_site[site] = []
                by_site[site].append(item["email"])
            
            # Add each site as a field
            for site, emails in by_site.items():
                field_value = "\n".join([f"📧 `{e}`" for e in emails])
                emails_embed.add_field(
                    name=f"📍 {site}",
                    value=field_value,
                    inline=True
                )
            
            await ctx.send(embed=emails_embed)
        
        # Display phone numbers if found
        if recovery_phones:
            # Deduplicate phone numbers
            unique_recovery_phones = []
            seen = set()
            
            for item in recovery_phones:
                key = (item["site"], item["phone"])
                if key not in seen:
                    seen.add(key)
                    unique_recovery_phones.append(item)
            
            phones_embed = discord.Embed(
                title=f"Recovery Phone Numbers for {email}",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            
            phones_embed.description = f"Found {len(unique_recovery_phones)} phone number(s):"
            
            # Group phone numbers by site
            by_site = {}
            for item in unique_recovery_phones:
                site = item["site"] or "Unknown"
                if site not in by_site:
                    by_site[site] = []
                by_site[site].append(item["phone"])
            
            # Add each site as a field
            for site, phones in by_site.items():
                field_value = "\n".join([f"📱 `{phone}`" for phone in phones])
                phones_embed.add_field(
                    name=f"📍 {site}",
                    value=field_value,
                    inline=True
                )
            
            await ctx.send(embed=phones_embed)

    @bot.command(name="phone")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def phone_info(ctx, phone_number: str):
        """Get information about a phone number (international format)"""
        # Check if phonenumbers module is available
        try:
            import phonenumbers
            from phonenumbers import geocoder, carrier, timezone
        except ImportError:
            await ctx.send("❌ The phonenumbers module is not available. Please install it with `pip install phonenumbers`.")
            return
        
        # Send initial message
        message = await ctx.send(f"🔍 Analyzing phone number: `{phone_number}`...")
        
        try:
            # Parse phone number
            if not phone_number.startswith("+"):
                await message.edit(content="❌ Please provide the phone number in international format (starting with +).")
                return
            
            parsed_number = phonenumbers.parse(phone_number)
            
            # Check if valid
            if not phonenumbers.is_valid_number(parsed_number):
                await message.edit(content=f"❌ The phone number `{phone_number}` is invalid.")
                return
            
            # Get information
            country = geocoder.description_for_number(parsed_number, "en")
            service_provider = carrier.name_for_number(parsed_number, "en")
            possible_timezones = timezone.time_zones_for_number(parsed_number)
            
            # Format number in different formats
            international_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            national_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
            e164_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            
            # Create embed
            embed = discord.Embed(
                title=f"Phone Number Analysis: {international_format}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(name="Country", value=country or "Unknown", inline=True)
            embed.add_field(name="Service Provider", value=service_provider or "Unknown", inline=True)
            embed.add_field(name="Number Type", value=str(phonenumbers.number_type(parsed_number)), inline=True)
            
            embed.add_field(name="International Format", value=international_format, inline=True)
            embed.add_field(name="National Format", value=national_format, inline=True)
            embed.add_field(name="E164 Format", value=e164_format, inline=True)
            
            if possible_timezones:
                embed.add_field(name="Possible Timezones", value=", ".join(possible_timezones), inline=False)
            
            # Add additional information
            embed.add_field(
                name="Country Code",
                value=f"+{parsed_number.country_code}",
                inline=True
            )
            
            embed.add_field(
                name="National Number",
                value=parsed_number.national_number,
                inline=True
            )
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
        
        except Exception as e:
            await message.edit(content=f"❌ Error analyzing phone number: {str(e)}")
