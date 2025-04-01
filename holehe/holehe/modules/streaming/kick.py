from holehe.core import *
from holehe.localuseragent import *
import json
import random

async def kick(email, client, out):
    name = "kick"
    domain = "kick.com"
    method = "register"
    frequent_rate_limit=False

    headers = {
        "User-agent": random.choice(ua["browsers"]["chrome"]),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://kick.com",
        "Referer": "https://kick.com/register"
    }
    
    try:
        print(f"[+] Checking {email} on {domain}")
        
        # First, load the registration page to get any cookies
        reg_page_url = "https://kick.com/register"
        try:
            reg_page = await client.get(reg_page_url, headers={
                "User-agent": random.choice(ua["browsers"]["chrome"]),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "DNT": "1"
            })
        except Exception as e:
            print(f"Error getting registration page: {e}")
            # Continue anyway, as we might not need cookies
        
        # Check if email is already registered during registration process
        check_url = "https://kick.com/api/v1/signup/check"
        
        # Create a username from the email
        username_base = email.split("@")[0]
        # Ensure it's between 3-25 chars as per Kick requirements
        username = username_base[:20] + "123" if len(username_base) < 3 else username_base[:20]
        
        data = {
            "username": username, 
            "email": email
        }
        
        # Convert data to JSON
        json_data = json.dumps(data)
        
        try:
            response = await client.post(check_url, headers=headers, data=json_data)
            
            # Try to parse the response as JSON
            try:
                json_response = response.json()
                
                # Debug print
                print(f"Kick API response: {json_response}")
                
                # If there's an error about the email, the account exists
                if 'email' in json_response and json_response['email'] and isinstance(json_response['email'], list):
                    for err in json_response['email']:
                        if "already been taken" in err.lower() or "already in use" in err.lower():
                            out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                                    "rateLimit": False,
                                    "exists": True,
                                    "emailrecovery": None,
                                    "phoneNumber": None,
                                    "others": None})
                            return
                
                # If no email error, or if "username" is the only field with an error, account doesn't exist
                out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                            "rateLimit": False,
                            "exists": False,
                            "emailrecovery": None,
                            "phoneNumber": None,
                            "others": None})
            except ValueError:
                # If the response isn't valid JSON, check the status code
                if response.status_code == 400:
                    # 400 likely means validation error - which could indicate account exists
                    out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                                "rateLimit": False,
                                "exists": True,
                                "emailrecovery": None,
                                "phoneNumber": None,
                                "others": None})
                elif response.status_code == 429:
                    # Rate limit
                    out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                                "rateLimit": True,
                                "exists": False,
                                "emailrecovery": None,
                                "phoneNumber": None,
                                "others": None})
                else:
                    # Unknown response, treat as rate limit
                    out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                                "rateLimit": True,
                                "exists": False,
                                "emailrecovery": None,
                                "phoneNumber": None,
                                "others": {"error": f"Non-JSON response with status {response.status_code}"}})
        except Exception as req_err:
            print(f"Error making kick.com API request: {req_err}")
            out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                        "rateLimit": True,
                        "exists": False,
                        "emailrecovery": None,
                        "phoneNumber": None,
                        "others": {"error": str(req_err)}})
    except Exception as e:
        print(f"General error in kick module: {e}")
        out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                    "rateLimit": True,
                    "exists": False,
                    "emailrecovery": None,
                    "phoneNumber": None,
                    "others": {"error": str(e)}})
