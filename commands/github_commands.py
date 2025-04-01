"""
GitHub-related commands for Vigil OSINT Bot
"""

import datetime
import requests
import discord
from discord.ext import commands

def register_github_commands(bot, github_token=None):
    @bot.command(name="gituser")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gituser(ctx, username: str):
        """Get information about a GitHub user"""
        await ctx.send(f"🔍 Searching GitHub for user: `{username}`...")
        
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        response = requests.get(f"https://api.github.com/users/{username}", headers=headers)
        
        if response.status_code == 404:
            await ctx.send(f"❌ GitHub user `{username}` not found.")
            return
        
        if response.status_code != 200:
            await ctx.send(f"❌ GitHub API error: {response.status_code} - {response.reason}")
            return
        
        user_data = response.json()
        
        # Create embed
        embed = discord.Embed(
            title=f"{user_data['login']} - GitHub Profile",
            url=user_data["html_url"],
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        if user_data["avatar_url"]:
            embed.set_thumbnail(url=user_data["avatar_url"])
        
        # Add fields
        if user_data["name"]:
            embed.add_field(name="Name", value=user_data["name"], inline=True)
        
        embed.add_field(name="Public Repos", value=user_data["public_repos"], inline=True)
        embed.add_field(name="Followers", value=user_data["followers"], inline=True)
        embed.add_field(name="Following", value=user_data["following"], inline=True)
        
        if user_data["bio"]:
            embed.add_field(name="Bio", value=user_data["bio"], inline=False)
        
        if user_data["email"]:
            embed.add_field(name="Email", value=user_data["email"], inline=True)
        
        if user_data["location"]:
            embed.add_field(name="Location", value=user_data["location"], inline=True)
        
        if user_data["company"]:
            embed.add_field(name="Company", value=user_data["company"], inline=True)
        
        if user_data["blog"]:
            embed.add_field(name="Website", value=user_data["blog"], inline=True)
        
        embed.add_field(
            name="Account Created",
            value=user_data["created_at"].split("T")[0],
            inline=True
        )
        
        embed.add_field(
            name="Last Updated",
            value=user_data["updated_at"].split("T")[0],
            inline=True
        )
        
        # Send the embed
        await ctx.send(embed=embed)

    @bot.command(name="gitemail")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gitemail(ctx, email: str):
        """Find a GitHub user by email address"""
        await ctx.send(f"🔍 Searching GitHub for email: `{email}`...")
        
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        response = requests.get(f"https://api.github.com/search/users?q={email}+in:email", headers=headers)
        
        if response.status_code != 200:
            await ctx.send(f"❌ GitHub API error: {response.status_code} - {response.reason}")
            return
        
        data = response.json()
        
        if data["total_count"] == 0:
            await ctx.send(f"❌ No GitHub users found with email `{email}`.")
            return
        
        embed = discord.Embed(
            title=f"GitHub Users with Email: {email}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        for user in data["items"][:5]:  # Limit to first 5 results
            embed.add_field(
                name=user["login"],
                value=f"[Profile]({user['html_url']})\nScore: {user['score']}",
                inline=True
            )
        
        if data["total_count"] > 5:
            embed.set_footer(text=f"Showing 5 of {data['total_count']} results.")
        
        await ctx.send(embed=embed)

    @bot.command(name="gitrepo")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def gitrepo(ctx, username: str, repo_name: str):
        """Get emails from a GitHub repository"""
        await ctx.send(f"🔍 Analyzing GitHub repository: `{username}/{repo_name}`...")
        
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        
        # Check if repo exists
        repo_response = requests.get(f"https://api.github.com/repos/{username}/{repo_name}", headers=headers)
        
        if repo_response.status_code == 404:
            await ctx.send(f"❌ Repository `{username}/{repo_name}` not found.")
            return
        
        if repo_response.status_code != 200:
            await ctx.send(f"❌ GitHub API error: {repo_response.status_code} - {repo_response.reason}")
            return
        
        # Get commits to extract emails
        commits_response = requests.get(
            f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=100",
            headers=headers
        )
        
        if commits_response.status_code != 200:
            await ctx.send(f"❌ GitHub API error when fetching commits: {commits_response.status_code} - {commits_response.reason}")
            return
        
        commits_data = commits_response.json()
        
        if not commits_data:
            await ctx.send(f"⚠️ No commits found in repository `{username}/{repo_name}`.")
            return
        
        # Extract unique emails from commits
        emails = {}
        for commit in commits_data:
            if commit["commit"]["author"]["email"]:
                email = commit["commit"]["author"]["email"]
                name = commit["commit"]["author"]["name"]
                if email not in emails:
                    emails[email] = {"name": name, "count": 0}
                emails[email]["count"] += 1
        
        if not emails:
            await ctx.send(f"⚠️ No emails found in repository `{username}/{repo_name}`.")
            return
        
        # Create and send embed
        embed = discord.Embed(
            title=f"Emails from {username}/{repo_name}",
            url=f"https://github.com/{username}/{repo_name}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="Repository", value=repo_name, inline=True)
        embed.add_field(name="Owner", value=username, inline=True)
        embed.add_field(name="Total Commits", value=len(commits_data), inline=True)
        
        # Add emails as fields
        email_text = ""
        for email, data in emails.items():
            email_text += f"**{data['name']}** - `{email}` ({data['count']} commits)\n"
        
        if len(email_text) > 1024:
            # Split into multiple fields if too long
            chunks = email_text.split("\n")
            current_chunk = ""
            chunk_count = 1
            
            for line in chunks:
                if len(current_chunk) + len(line) + 1 > 1024:
                    embed.add_field(name=f"Emails (Part {chunk_count})", value=current_chunk, inline=False)
                    chunk_count += 1
                    current_chunk = line
                else:
                    if current_chunk:
                        current_chunk += "\n" + line
                    else:
                        current_chunk = line
            
            if current_chunk:
                embed.add_field(name=f"Emails (Part {chunk_count})", value=current_chunk, inline=False)
        else:
            embed.add_field(name="Emails", value=email_text, inline=False)
        
        await ctx.send(embed=embed)

    @bot.command(name="gitrepos")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def gitrepos(ctx, username: str):
        """Analyze all repositories of a GitHub user"""
        await ctx.send(f"🔍 Analyzing repositories for GitHub user: `{username}`...")
        
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        
        # Check if user exists
        user_response = requests.get(f"https://api.github.com/users/{username}", headers=headers)
        
        if user_response.status_code == 404:
            await ctx.send(f"❌ GitHub user `{username}` not found.")
            return
        
        if user_response.status_code != 200:
            await ctx.send(f"❌ GitHub API error: {user_response.status_code} - {user_response.reason}")
            return
        
        user_data = user_response.json()
        
        # Get repositories
        repos_response = requests.get(
            f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
            headers=headers
        )
        
        if repos_response.status_code != 200:
            await ctx.send(f"❌ GitHub API error when fetching repositories: {repos_response.status_code} - {repos_response.reason}")
            return
        
        repos_data = repos_response.json()
        
        if not repos_data:
            await ctx.send(f"⚠️ No public repositories found for user `{username}`.")
            return
        
        # Create initial embed
        embed = discord.Embed(
            title=f"GitHub Repositories for {username}",
            url=f"https://github.com/{username}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        if user_data.get("avatar_url"):
            embed.set_thumbnail(url=user_data["avatar_url"])
        
        embed.add_field(name="Total Public Repos", value=user_data["public_repos"], inline=True)
        embed.add_field(name="Showing", value=f"{len(repos_data)} most recent", inline=True)
        
        await ctx.send(embed=embed)
        
        # List repositories in chunks (Discord has 25 field limit for embeds)
        chunks = [repos_data[i:i+8] for i in range(0, len(repos_data), 8)]
        
        for i, chunk in enumerate(chunks):
            repos_embed = discord.Embed(
                title=f"Repositories for {username} (Page {i+1}/{len(chunks)})",
                color=discord.Color.blue()
            )
            
            for repo in chunk:
                value = (
                    f"⭐ {repo['stargazers_count']} | 🍴 {repo['forks_count']}\n"
                    f"📅 Updated: {repo['updated_at'].split('T')[0]}\n"
                    f"📝 {repo['description'] if repo['description'] else 'No description'}"
                )
                repos_embed.add_field(
                    name=repo["name"],
                    value=value,
                    inline=False
                )
            
            await ctx.send(embed=repos_embed)

    @bot.command(name="gitkeys")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def gitkeys(ctx, username: str):
        """Find GPG and SSH keys for a GitHub user"""
        await ctx.send(f"🔍 Searching for GitHub keys for user: `{username}`...")
        
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        
        # Check if user exists
        user_response = requests.get(f"https://api.github.com/users/{username}", headers=headers)
        
        if user_response.status_code == 404:
            await ctx.send(f"❌ GitHub user `{username}` not found.")
            return
        
        if user_response.status_code != 200:
            await ctx.send(f"❌ GitHub API error: {user_response.status_code} - {user_response.reason}")
            return
        
        # Get GPG keys
        gpg_response = requests.get(f"https://api.github.com/users/{username}/gpg_keys", headers=headers)
        
        if gpg_response.status_code != 200:
            await ctx.send(f"❌ GitHub API error when fetching GPG keys: {gpg_response.status_code} - {gpg_response.reason}")
            return
        
        gpg_data = gpg_response.json()
        
        # Get SSH keys
        ssh_response = requests.get(f"https://api.github.com/users/{username}/keys", headers=headers)
        
        if ssh_response.status_code != 200:
            await ctx.send(f"❌ GitHub API error when fetching SSH keys: {ssh_response.status_code} - {ssh_response.reason}")
            return
        
        ssh_data = ssh_response.json()
        
        # Create embed
        embed = discord.Embed(
            title=f"GitHub Keys for {username}",
            url=f"https://github.com/{username}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        if gpg_data:
            gpg_keys_text = ""
            for key in gpg_data:
                key_id = key.get("key_id", "Unknown")
                created = key.get("created_at", "Unknown").split("T")[0]
                gpg_keys_text += f"Key ID: `{key_id}` | Created: {created}\n"
            
            embed.add_field(name=f"GPG Keys ({len(gpg_data)})", value=gpg_keys_text or "None", inline=False)
        else:
            embed.add_field(name="GPG Keys", value="No GPG keys found", inline=False)
        
        if ssh_data:
            ssh_keys_text = ""
            for i, key in enumerate(ssh_data):
                key_fragment = key.get("key", "").split(" ")[0]
                ssh_keys_text += f"Key {i+1}: `{key_fragment}...`\n"
            
            embed.add_field(name=f"SSH Keys ({len(ssh_data)})", value=ssh_keys_text or "None", inline=False)
        else:
            embed.add_field(name="SSH Keys", value="No SSH keys found", inline=False)
        
        await ctx.send(embed=embed)
