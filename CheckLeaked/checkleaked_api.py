#!/usr/bin/env python3
"""
CheckLeaked API Client
Provides an interface to interact with breach data search functionality
"""

import requests
import json
import logging
from urllib.parse import quote

# Configure logging
logger = logging.getLogger("checkleaked_api")

class CheckLeakedAPI:
    """Client for interacting with breach data search API"""
    
    # Map of search types and their descriptions for better usability
    DEHASHED_SEARCH_TYPES = {
        "email": "Email address",
        "username": "Username or account name",
        "ip_address": "IP address",
        "name": "Person's name",
        "address": "Physical address",
        "phone": "Phone number",
        "vin": "Vehicle identification number",
        "free": "Free-text search"
    }
    
    EXPERIMENTAL_SEARCH_TYPES = {
        "username": "Username across multiple breach databases",
        "mass": "Mass query across multiple data sources",
        "email": "Email with enhanced results",
        "lastip": "Last known IP address for a target",
        "password": "Plain text password",
        "name": "Person's name with enhanced results",
        "hash": "Password hash"
    }
    
    LEAKCHECK_SEARCH_TYPES = {
        "email": "Email address",
        "mass": "Mass search across multiple data sources",
        "hash": "Password hash",
        "pass_email": "Password and email combination",
        "phash": "Partial hash",
        "domain_email": "Email domain",
        "login": "Username/login",
        "phone": "Phone number",
        "mc": "Minecraft username",
        "pass_login": "Password and login combination",
        "pass_phone": "Password and phone combination",
        "auto": "Auto-detect type"
    }
    
    def __init__(self, api_key):
        """Initialize with API key"""
        self.api_key = api_key
        self.base_url = "https://api.checkleaked.cc/api"
        self.headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }
    
    def search_dehashed(self, entry, search_type, page=1):
        """
        Search the Dehashed database
        
        Args:
            entry (str): Search entry (email, username, etc.)
            search_type (str): Type of search (email, username, ip_address, etc.)
            page (int): Page number for results
            
        Returns:
            dict: API response
        """
        endpoint = f"{self.base_url}/dehashed"
        
        # Validate search type
        valid_types = list(self.DEHASHED_SEARCH_TYPES.keys())
        if search_type not in valid_types:
            raise ValueError(f"Invalid search type for Dehashed. Must be one of: {', '.join(valid_types)}")
        
        payload = {
            "entry": entry,
            "type": search_type,
            "page": page
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Dehashed: {str(e)}")
            if response.text:
                logger.error(f"Response: {response.text}")
            # Try to extract more detailed error info if possible
            error_message = str(e)
            try:
                if hasattr(response, 'json'):
                    error_json = response.json()
                    if 'message' in error_json:
                        error_message = f"{error_message}: {error_json['message']}"
                    elif 'error' in error_json:
                        error_message = f"{error_message}: {error_json['error']}"
            except:
                pass
                
            return {"error": error_message, "status": "failed"}
    
    def search_experimental(self, entry, search_type):
        """
        Use the experimental search functionality
        
        Args:
            entry (str): Search entry
            search_type (str): Type of search
            
        Returns:
            dict: API response
        """
        endpoint = f"{self.base_url}/experimental"
        
        # Validate search type
        valid_types = list(self.EXPERIMENTAL_SEARCH_TYPES.keys())
        if search_type not in valid_types:
            raise ValueError(f"Invalid search type for Experimental. Must be one of: {', '.join(valid_types)}")
        
        payload = {
            "entry": entry,
            "type": search_type
        }
        
        try:
            # Log the request payload
            logger.info(f"Making experimental search request with payload: {json.dumps(payload)}")
            
            response = requests.post(endpoint, headers=self.headers, json=payload)
            
            # Log the raw response status and headers
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            # Get the response text for debug purposes
            response_text = response.text
            logger.info(f"Response text: {response_text[:500]}...")
            
            # Check if the response contains valid JSON
            if response_text and response_text.strip():
                try:
                    result = response.json()
                    # Normalize the response - different APIs use different field names
                    if 'results' in result and 'data' not in result:
                        result['data'] = result['results']
                    elif 'result' in result and 'data' not in result:
                        result['data'] = result['result']
                    return result
                except json.JSONDecodeError as jde:
                    logger.error(f"Invalid JSON in response: {str(jde)}")
                    return {"error": f"API returned invalid JSON: {str(jde)}", "status": "failed"}
            else:
                logger.error("Empty response from API")
                return {"error": "API returned empty response", "status": "failed"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error using experimental search: {str(e)}")
            try:
                error_message = str(e)
                if hasattr(response, 'text') and response.text:
                    logger.error(f"Response: {response.text}")
                    
                if hasattr(response, 'json'):
                    try:
                        error_json = response.json()
                        if 'message' in error_json:
                            error_message = f"{error_message}: {error_json['message']}"
                        elif 'error' in error_json:
                            error_message = f"{error_message}: {error_json['error']}"
                    except:
                        pass
            except:
                pass
                
            return {"error": error_message, "status": "failed"}
    
    def crack_hash(self, hash_value):
        """
        Attempt to crack a hash
        
        Args:
            hash_value (str): Hash to crack
            
        Returns:
            dict: API response
        """
        endpoint = f"{self.base_url}/crack_hash"
        
        payload = {
            "hash": hash_value
        }
        
        try:
            # Log the request details
            logger.info(f"Making hash cracking request for hash: {hash_value}")
            
            # Make API request
            response = requests.post(endpoint, headers=self.headers, json=payload)
            
            # Log response details
            logger.info(f"Hash crack response status: {response.status_code}")
            logger.info(f"Hash crack response headers: {response.headers}")
            
            # Get the response text
            response_text = response.text
            logger.info(f"Hash crack response text: {response_text[:500]}...")
            
            # Process the response
            if response.status_code == 200 and response_text and response_text.strip():
                try:
                    # Try to parse the JSON response
                    result = response.json()
                    
                    # Log the parsed result
                    logger.info(f"Parsed hash crack result: {json.dumps(result, indent=2)}")
                    
                    # If we have a result or error field, return it
                    return result
                except json.JSONDecodeError as jde:
                    logger.error(f"Invalid JSON in hash crack response: {str(jde)}")
                    return {"error": f"API returned invalid JSON: {str(jde)}", "status": "failed"}
            else:
                # Handle empty responses or non-200 status codes
                logger.error(f"Error response from hash crack API: Status {response.status_code}")
                return {"error": f"API returned status code {response.status_code}", "status": "failed"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception in hash crack: {str(e)}")
            
            # Try to gather more error details if possible
            error_message = str(e)
            try:
                if 'response' in locals() and hasattr(response, 'text') and response.text:
                    logger.error(f"Error response: {response.text}")
                    
                if 'response' in locals() and hasattr(response, 'json'):
                    try:
                        error_json = response.json()
                        if 'message' in error_json:
                            error_message = f"{error_message}: {error_json['message']}"
                        elif 'error' in error_json:
                            error_message = f"{error_message}: {error_json['error']}"
                    except:
                        pass
            except:
                pass
                
            return {"error": error_message, "status": "failed"}
    
    def get_search_types(self, search_category="dehashed"):
        """
        Get a list of valid search types with descriptions
        
        Args:
            search_category (str): The category of search types to return
                                  ("dehashed", "experimental", or "leakcheck")
                                  
        Returns:
            dict: Dictionary mapping search types to their descriptions
        """
        if search_category.lower() == "dehashed":
            return self.DEHASHED_SEARCH_TYPES
        elif search_category.lower() == "experimental":
            return self.EXPERIMENTAL_SEARCH_TYPES
        elif search_category.lower() == "leakcheck":
            return self.LEAKCHECK_SEARCH_TYPES
        else:
            return {}
    
    def leakcheck_search(self, leak_check_key, check_value, check_type):
        """
        Search in LeakCheck
        
        Args:
            leak_check_key (str): LeakCheck API key
            check_value (str): Value to check
            check_type (str): Type of check
            
        Returns:
            dict: API response
        """
        endpoint = f"{self.base_url}/leak_check"
        
        # Validate check type
        valid_types = list(self.LEAKCHECK_SEARCH_TYPES.keys())
        if check_type not in valid_types:
            raise ValueError(f"Invalid check type for LeakCheck. Must be one of: {', '.join(valid_types)}")
        
        params = {
            "key": leak_check_key,
            "check": check_value,
            "type": check_type
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching LeakCheck: {str(e)}")
            if response.text:
                logger.error(f"Response: {response.text}")
            # Try to extract more detailed error info if possible
            error_message = str(e)
            try:
                if hasattr(response, 'json'):
                    error_json = response.json()
                    if 'message' in error_json:
                        error_message = f"{error_message}: {error_json['message']}"
                    elif 'error' in error_json:
                        error_message = f"{error_message}: {error_json['error']}"
            except:
                pass
                
            return {"error": error_message, "status": "failed"}
