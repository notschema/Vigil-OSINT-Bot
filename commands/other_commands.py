"""
Other miscellaneous commands for Vigil OSINT Bot
"""

import datetime
import discord
import io
import contextlib
from discord.ext import commands

from .utils import xeuledoc_available, chunk_message

def register_other_commands(bot):
    @bot.command(name="gdoc", aliases=["xeuledoc"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def gdoc_info(ctx, google_doc_link: str):
        """Get information about a Google Document"""
        if not xeuledoc_available:
            await ctx.send("❌ The XeuleDoc module is not available. This command will not work.")
            return
        
        # Validate link
        if "docs.google.com" not in google_doc_link:
            await ctx.send("❌ Invalid Google Doc link. Please provide a valid docs.google.com URL.")
            return
        
        # Send initial message
        message = await ctx.send(f"🔍 Analyzing Google Document: `{google_doc_link}`...")
        
        try:
            # Create a string buffer to capture stdout
            output_buffer = io.StringIO()
            
            # Capture all stdout output from the doc_hunt function
            with contextlib.redirect_stdout(output_buffer):
                # Import here to avoid circular imports
                from xeuledoc.core import doc_hunt, TMPrinter
                
                # Run doc_hunt with a standard TMPrinter
                tmprinter = TMPrinter()
                doc_hunt(google_doc_link, tmprinter)
            
            # Get the captured output
            output = output_buffer.getvalue()
            
            # Create embed
            embed = discord.Embed(
                title="Google Document Analysis",
                description=f"[View Document]({google_doc_link})",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            
            # Process the output
            if not output:
                embed.add_field(name="Error", value="No data returned from the analysis", inline=False)
                await message.edit(content=None, embed=embed)
                return
            
            # Parse data from output
            doc_id = None
            created_date = None
            modified_date = None
            owner_name = None
            owner_email = None
            owner_id = None
            public_permissions = []
            
            # Split into lines for processing
            lines = output.strip().split('\n')
            
            in_permissions_section = False
            in_owner_section = False
            
            for line in lines:
                line = line.strip()
                
                if "Document ID :" in line:
                    doc_id = line.split("Document ID :")[1].strip()
                elif "[+] Creation date :" in line:
                    created_date = line.split("[+] Creation date :")[1].strip()
                elif "[+] Last edit date :" in line:
                    modified_date = line.split("[+] Last edit date :")[1].strip()
                elif "Public permissions :" in line:
                    in_permissions_section = True
                    in_owner_section = False
                elif "[+] Owner found !" in line:
                    in_permissions_section = False
                    in_owner_section = True
                elif line.startswith("Name :") and in_owner_section:
                    owner_name = line.split("Name :")[1].strip()
                elif line.startswith("Email :") and in_owner_section:
                    owner_email = line.split("Email :")[1].strip()
                elif line.startswith("Google ID :") and in_owner_section:
                    owner_id = line.split("Google ID :")[1].strip()
                elif line.startswith("- ") and in_permissions_section:
                    permission = line[2:].strip()
                    public_permissions.append(permission)
            
            # Add fields to embed
            if doc_id:
                embed.add_field(name="Document ID", value=f"`{doc_id}`", inline=False)
            
            if created_date:
                embed.add_field(name="Created", value=created_date, inline=True)
            
            if modified_date:
                embed.add_field(name="Last Modified", value=modified_date, inline=True)
            
            if public_permissions:
                embed.add_field(name="Public Permissions", 
                               value=", ".join(public_permissions), 
                               inline=True)
            
            if owner_name:
                embed.add_field(name="Owner", value=owner_name, inline=True)
            
            if owner_email:
                embed.add_field(name="Email", value=owner_email, inline=True)
            
            if owner_id:
                embed.add_field(name="Google ID", value=owner_id, inline=True)
            
            # If we couldn't parse any structured data, show the raw output
            if not any([created_date, modified_date, owner_name, owner_email, public_permissions]):
                # Discord has a 1024 character limit per field
                if len(output) <= 1024:
                    embed.add_field(name="Raw Data", value=f"```\n{output}\n```", inline=False)
                else:
                    # Split long output into multiple fields
                    chunks = chunk_message(output, 1000)  # Leave room for the code block formatting
                    for i, chunk in enumerate(chunks):
                        embed.add_field(name=f"Raw Data (Part {i+1})", value=f"```\n{chunk}\n```", inline=False)
            
            # Update message with embed
            await message.edit(content=None, embed=embed)
        
        except Exception as e:
            await message.edit(content=f"❌ Error analyzing Google Document: {str(e)}")

    @bot.command(name="weather")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def weather_info(ctx, city: str, date: str = None):
        """Get historical weather data for a location and date"""
        await ctx.send("🚧 The weather information feature is under development. Please check back later.")
