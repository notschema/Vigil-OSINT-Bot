# Vigil OSINT Bot - Development Roadmap

This document outlines the planned features and improvements for the Vigil OSINT Bot.

## Current Status

The Vigil OSINT Bot currently has the following functionality:
- GitHub OSINT integration (users, emails, repositories)
- Username search via Sherlock, WhatsMyName, and Masto
- Basic phone number analysis
- Breach data search through CheckLeaked integration

## Roadmap Items

### Short-term Goals

1. **Dependencies Installation**
   - Ensure all required packages are installed: `pip install -r requirements.txt`
   - Specific packages needed:
     - `holehe==1.61` - For email verification
     - `socialscan` - For social media username verification
     - `toutatis==1.24` - For Instagram analysis
     - `xeuledoc` - For Google document analysis
     - `maigret==0.4.4` - For comprehensive username searches

2. **API Integration**
   - Set up environment variables for API keys:
     ```
     DISCORD_TOKEN=your_discord_token
     GITHUB_TOKEN=your_github_token
     ```

3. **Command Enhancements**
   - Improve error handling and user feedback
   - Add more detailed help documentation

### Medium-term Goals

1. **Weather API Integration**
   - Implement the `!weather` command with a proper weather API
   - Options include OpenWeatherMap, Visual Crossing, or WeatherAPI
   - Create a dedicated weather.py module

2. **Twitter/X History Implementation**
   - Implement the `!twitter` command with historical username data
   - Explore API options or historical databases

3. **Google Doc Analysis**
   - Complete the `!gdoc` command with full xeuledoc integration
   - Set up browser automation for document analysis

### Long-term Goals

1. **Custom Dashboard**
   - Create a web dashboard for viewing comprehensive OSINT results
   - Allow exporting and saving of search results

2. **Advanced Reporting**
   - Generate PDF reports of OSINT findings
   - Add visualization options for data

3. **Additional Data Sources**
   - Blockchain/cryptocurrency analysis
   - Dark web monitoring
   - Additional social media platforms

## How to Contribute

If you'd like to contribute to the development of Vigil OSINT Bot:

1. Select an item from the roadmap
2. Create a fork of the repository
3. Implement the feature or enhancement
4. Submit a pull request

## Priority Items

The following items are currently our highest priorities:
1. Ensuring all dependencies are properly installed
2. Completing the Twitter history command
3. Implementing the weather API integration

Last Updated: March 2025
