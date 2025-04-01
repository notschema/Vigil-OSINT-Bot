from holehe.core import *
from holehe.localuseragent import *
import random
import logging

async def amazon_au(email, client, out):
    name = "amazon_au"
    domain = "amazon.com.au"
    method = "login"
    frequent_rate_limit=True  # Amazon often rate-limits

    headers = {
        "User-agent": random.choice(ua["browsers"]["chrome"]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.amazon.com.au/",
        "Origin": "https://www.amazon.com.au",
        "DNT": "1"
    }
    try:
        # Log that this module is being called
        print(f"[+] Checking {email} on {domain}")
        
        # First request - get the signin page to get CSRF tokens and cookies
        url = "https://www.amazon.com.au/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com.au%2F%3F_encoding%3DUTF8%26ref_%3Dnav_ya_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=auflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&"
        req = await client.get(url, headers=headers)
        
        # Extract CSRF and other form data
        body = BeautifulSoup(req.text, 'html.parser')
        
        # Check if we got a proper response
        if not body or 'form' not in req.text.lower():
            out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                    "rateLimit": True,
                    "exists": False,
                    "emailrecovery": None,
                    "phoneNumber": None,
                    "others": {"error": "Failed to load Amazon login page"}})
            return
        
        # Extract form data
        try:
            form_data = dict([(x["name"], x["value"]) for x in body.select('form input') if ('name' in x.attrs and 'value' in x.attrs)])
            form_data["email"] = email
        except Exception as form_error:
            out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                    "rateLimit": True,
                    "exists": False,
                    "emailrecovery": None,
                    "phoneNumber": None,
                    "others": {"error": f"Form parsing error: {str(form_error)}"}})
            return
        
        # Post the form data to check if the account exists
        try:
            signin_url = 'https://www.amazon.com.au/ap/signin'
            req = await client.post(signin_url, data=form_data, headers=headers)
            response_body = BeautifulSoup(req.text, 'html.parser')
            
            # Look for password prompt (indicating account exists)
            if response_body.find("div", {"id": "auth-password-missing-alert"}) or "enter your password" in req.text.lower():
                out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                        "rateLimit": False,
                        "exists": True,
                        "emailrecovery": None,
                        "phoneNumber": None,
                        "others": None})
            # Check for specific "no account" messages
            elif "we cannot find an account with that email address" in req.text.lower():
                out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                        "rateLimit": False,
                        "exists": False,
                        "emailrecovery": None,
                        "phoneNumber": None,
                        "others": None})
            # Check for CAPTCHA or other error
            elif "important message" in req.text.lower() or "captcha" in req.text.lower():
                out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                        "rateLimit": True,
                        "exists": False,
                        "emailrecovery": None,
                        "phoneNumber": None,
                        "others": {"error": "Captcha or security check encountered"}})
            else:
                # If no clear indicators, assume not found
                out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                        "rateLimit": False,
                        "exists": False,
                        "emailrecovery": None,
                        "phoneNumber": None,
                        "others": None})
        except Exception as post_error:
            out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                    "rateLimit": True,
                    "exists": False,
                    "emailrecovery": None,
                    "phoneNumber": None,
                    "others": {"error": f"Post request error: {str(post_error)}"}})
    except Exception as e:
        out.append({"name": name,"domain":domain,"method":method,"frequent_rate_limit":frequent_rate_limit,
                    "rateLimit": True,
                    "exists": False,
                    "emailrecovery": None,
                    "phoneNumber": None,
                    "others": {"error": str(e)}})
