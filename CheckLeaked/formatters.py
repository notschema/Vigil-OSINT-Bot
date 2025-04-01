"""
Formatters for presenting CheckLeaked API results in Discord
"""

import discord
import json
from datetime import datetime
from typing import Dict, List, Any, Union

def format_dehashed_results(results: Dict, query: str, query_type: str) -> discord.Embed:
    """
    Format Dehashed results for Discord
    
    Args:
        results: The API response
        query: The search query
        query_type: The type of search
        
    Returns:
        Discord Embed with formatted results
    """
    embed = discord.Embed(
        title=f"Breach Data Results for: {query}",
        color=0xFF5733,  # Orange color
        description=f"Data breach search results for {query_type}: `{query}`"
    )
    
    # Check for errors
    if results.get("error"):
        embed.add_field(
            name="Error",
            value=f"An error occurred: {results['error']}",
            inline=False
        )
        return embed
    
    # Get basic stats
    total_results = results.get("total", 0)
    entries = results.get("entries", [])
    
    embed.add_field(
        name="Statistics",
        value=f"Found {total_results} results in data breaches",
        inline=False
    )
    
    # Add up to 10 entries to avoid embed size limits
    for i, entry in enumerate(entries[:10]):
        # Format each entry
        entry_text = ""
        
        if entry.get("email"):
            entry_text += f"Email: `{entry['email']}`\n"
        
        if entry.get("username"):
            entry_text += f"Username: `{entry['username']}`\n"
        
        if entry.get("password"):
            entry_text += f"Password: ||`{entry['password']}`||\n"
        
        if entry.get("hashed_password"):
            entry_text += f"Hash: `{entry['hashed_password']}`\n"
        
        if entry.get("ip_address"):
            entry_text += f"IP: `{entry['ip_address']}`\n"
        
        if entry.get("name"):
            entry_text += f"Name: `{entry['name']}`\n"
        
        if entry.get("breach") or entry.get("source"):
            source = entry.get("breach") or entry.get("source")
            entry_text += f"Source: `{source}`\n"
        
        if entry.get("date") or entry.get("last_breach"):
            date = entry.get("date") or entry.get("last_breach")
            entry_text += f"Date: `{date}`\n"
        
        # Add the entry to the embed
        if entry_text:
            embed.add_field(
                name=f"Result {i+1}",
                value=entry_text,
                inline=False
            )
    
    # Add note if results were truncated
    if len(entries) > 10:
        embed.set_footer(text=f"Showing 10/{len(entries)} results. Use specific queries for more targeted results.")
    
    return embed

def format_experimental_results(results: Dict, query: str, query_type: str) -> discord.Embed:
    """
    Format experimental search results for Discord
    
    Args:
        results: The API response
        query: The search query
        query_type: The type of search
        
    Returns:
        Discord Embed with formatted results
    """
    embed = discord.Embed(
        title=f"Advanced Breach Search: {query}",
        color=0x3498DB,  # Blue color
        description=f"Advanced search results for {query_type}: `{query}`"
    )
    
    # Check for errors
    if results.get("error"):
        embed.add_field(
            name="Error",
            value=f"An error occurred: {results['error']}",
            inline=False
        )
        return embed
    
    # Process results - structure depends on the actual API response
    # This is a generic handler that tries to accommodate various response formats
    
    if isinstance(results, dict):
        # Process dictionary results
        for key, value in results.items():
            if key.lower() in ["error", "status", "message"]:
                continue
                
            if isinstance(value, list) and len(value) > 0:
                # Handle list of results
                embed.add_field(
                    name=f"{key.replace('_', ' ').title()}",
                    value=f"Found {len(value)} results",
                    inline=False
                )
                
                # Add up to 5 entries from this category
                for i, entry in enumerate(value[:5]):
                    if isinstance(entry, dict):
                        entry_text = "\n".join([f"{k}: `{v}`" for k, v in entry.items() if v and k != "id"])
                        embed.add_field(
                            name=f"{key.title()} {i+1}",
                            value=entry_text or "No details available",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name=f"{key.title()} {i+1}",
                            value=f"`{entry}`",
                            inline=True
                        )
            elif isinstance(value, dict):
                # Handle dictionary values
                entry_text = "\n".join([f"{k}: `{v}`" for k, v in value.items() if v])
                embed.add_field(
                    name=key.replace("_", " ").title(),
                    value=entry_text or "No details available",
                    inline=False
                )
            else:
                # Handle simple values
                embed.add_field(
                    name=key.replace("_", " ").title(),
                    value=f"`{value}`",
                    inline=True
                )
    elif isinstance(results, list) and len(results) > 0:
        # Process list results
        embed.add_field(
            name="Results",
            value=f"Found {len(results)} entries",
            inline=False
        )
        
        # Add up to 10 entries
        for i, entry in enumerate(results[:10]):
            if isinstance(entry, dict):
                entry_text = "\n".join([f"{k}: `{v}`" for k, v in entry.items() if v and k != "id"])
                embed.add_field(
                    name=f"Result {i+1}",
                    value=entry_text or "No details available",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"Result {i+1}",
                    value=f"`{entry}`",
                    inline=True
                )
    else:
        # Handle unexpected result format
        embed.add_field(
            name="Results",
            value="No results found or unexpected response format",
            inline=False
        )
    
    return embed

def format_hash_crack_results(results: Dict, hash_value: str) -> discord.Embed:
    """
    Format hash cracking results for Discord
    
    Args:
        results: The API response
        hash_value: The hash that was attempted to be cracked
        
    Returns:
        Discord Embed with formatted results
    """
    embed = discord.Embed(
        title=f"Hash Cracking Results",
        color=0x2ECC71,  # Green color
        description=f"Results for hash: `{hash_value}`"
    )
    
    # Check for errors
    if results.get("error"):
        embed.add_field(
            name="Error",
            value=f"An error occurred: {results['error']}",
            inline=False
        )
        return embed
    
    # Extract the cracked value - the structure depends on the actual API response
    cracked_value = None
    
    if results.get("password") or results.get("cracked") or results.get("plaintext"):
        cracked_value = results.get("password") or results.get("cracked") or results.get("plaintext")
    elif isinstance(results, dict):
        # Try to find any field that might contain the password
        for key, value in results.items():
            if key.lower() in ["password", "cracked", "plaintext", "result", "plain"]:
                cracked_value = value
                break
    
    if cracked_value:
        embed.add_field(
            name="Cracked Value",
            value=f"||`{cracked_value}`||",
            inline=False
        )
        embed.add_field(
            name="Hash",
            value=f"`{hash_value}`",
            inline=False
        )
        embed.color = 0x2ECC71  # Green for success
    else:
        embed.add_field(
            name="Result",
            value="Hash could not be cracked",
            inline=False
        )
        embed.add_field(
            name="Hash",
            value=f"`{hash_value}`",
            inline=False
        )
        embed.color = 0xE74C3C  # Red for failure
    
    # Add any additional information from the response
    for key, value in results.items():
        if key.lower() not in ["password", "cracked", "plaintext", "error", "status", "hash"]:
            embed.add_field(
                name=key.replace("_", " ").title(),
                value=f"`{value}`",
                inline=True
            )
    
    return embed

def format_leak_check_results(results: Dict, check_value: str, check_type: str) -> discord.Embed:
    """
    Format LeakCheck results for Discord
    
    Args:
        results: The API response
        check_value: The value that was checked
        check_type: The type of check
        
    Returns:
        Discord Embed with formatted results
    """
    embed = discord.Embed(
        title=f"LeakCheck Results",
        color=0x9B59B6,  # Purple color
        description=f"Leak check results for {check_type}: `{check_value}`"
    )
    
    # Check for errors
    if results.get("error"):
        embed.add_field(
            name="Error",
            value=f"An error occurred: {results['error']}",
            inline=False
        )
        return embed
    
    # Handle the LeakCheck response - structure depends on the actual API response
    if results.get("found") is not None:
        embed.add_field(
            name="Status",
            value=f"Found: {'Yes' if results['found'] else 'No'}",
            inline=False
        )
    
    if results.get("sources") and isinstance(results["sources"], list):
        sources = results["sources"]
        embed.add_field(
            name="Sources",
            value=f"Found in {len(sources)} breach sources",
            inline=False
        )
        
        # Add up to 10 sources
        for i, source in enumerate(sources[:10]):
            if isinstance(source, dict):
                source_text = ""
                if source.get("name"):
                    source_text += f"Name: `{source['name']}`\n"
                if source.get("date"):
                    source_text += f"Date: `{source['date']}`\n"
                if source.get("password") or source.get("line"):
                    password = source.get("password") or source.get("line")
                    source_text += f"Password: ||`{password}`||\n"
                
                embed.add_field(
                    name=f"Source {i+1}",
                    value=source_text or "No details available",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"Source {i+1}",
                    value=f"`{source}`",
                    inline=True
                )
    
    # Add note if sources were truncated
    if results.get("sources") and isinstance(results["sources"], list) and len(results["sources"]) > 10:
        embed.set_footer(text=f"Showing 10/{len(results['sources'])} sources.")
    
    return embed
