# VIGIL OSINT BOT - COMMANDS REFERENCE

## General Commands

`!help` - Show help information for all commands
`!help <command>` - Show detailed help for a specific command
`!ping` - Check the bot's response time
`!about` - Show information about the bot

## GitHub Commands

`!gituser <username>` - Get information about a GitHub user
> Example: `!gituser octocat`

`!gitemail <email>` - Find a GitHub user by email address
> Example: `!gitemail example@github.com`

`!gitrepo <username> <repo_name>` - Get emails from a GitHub repository
> Example: `!gitrepo notschema vigil-osint`

`!gitrepos <username>` - Analyze all repositories of a GitHub user
> Example: `!gitrepos notschema`

`!gitkeys <username>` - Find GPG and SSH keys for a GitHub user
> Example: `!gitkeys octocat`

## Username Search Commands

`!sherlock <username>` - Search for username across multiple platforms (alias: `!sh`)
> Example: `!sherlock johndoe`

`!wmn <username>` - Search for username using WhatsMyName (alias: `!whatsmyname`)
> Example: `!wmn johndoe`

`!masto <username>` - Search for username across Mastodon instances
> Example: `!masto johndoe`

`!maigret <username>` - Search for username across 2500+ sites
> Example: `!maigret johndoe`

`!twitter <username>` - Search for historical Twitter usernames (alias: `!twit`)
> Example: `!twitter johndoe`

`!insta <username> [session_id]` - Extract Instagram account info (alias: `!instagram`)
> Example: `!insta johndoe`
> Example with session: `!insta johndoe ABC123XYZ`

`!socialscan <username> [username2]` - Check username availability (alias: `!social`)
> Example single: `!socialscan johndoe`
> Example double: `!socialscan johndoe janedoe`

## Email Commands

`!gmail <email>` - Check if a Gmail address is valid and deliverable
> Example: `!gmail johndoe@gmail.com`

`!email <email>` - Check which websites an email is registered on
> Example: `!email example@domain.com`

## Phone Investigation

`!phone <phone_number>` - Get information about a phone number (international format)
> Example: `!phone +12125551234`

## Breach Data Commands

`!breach <query> <type>` - Search for data in breaches
> Example: `!breach johndoe@example.com email`
> Example: `!breach johndoe username`
> Valid types: email, username, ip_address, name, address, phone, vin, free

`!breachadv <query> <type>` - Advanced breach data search (alias: `!advbreach`)
> Example: `!breachadv johndoe@example.com email`
> Example: `!breachadv password123 password`
> Valid types: username, mass, email, lastip, password, name, hash

`!crackhash <hash>` - Attempt to crack a hash
> Example: `!crackhash 5f4dcc3b5aa765d61d8327deb882cf99`

## Other Commands

`!gdoc <google_doc_link>` - Get information about a Google Document (alias: `!xeuledoc`)
> Example: `!gdoc https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/edit`

`!weather <city> <date>` - Get historical weather data for a location and date
> Example: `!weather "New York" 2023-09-15`

## Notes

1. Commands have cooldowns to prevent abuse and API rate limits
2. Some commands require API keys or additional configuration
3. Use `!help <command>` for detailed usage information
4. Commands with [square brackets] indicate optional parameters

## Usage Tips

- For the best results with username searches, try multiple tools (`!sherlock`, `!wmn`, `!maigret`)
- When searching for emails, always use `!email` to find account registrations
- For GitHub investigations, start with `!gituser` and then explore with `!gitrepos` and `!gitkeys`
- When searching phone numbers, always include the country code with a + symbol
