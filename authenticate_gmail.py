#!/usr/bin/env python
"""
Gmail API Manual Authentication Script

This script generates an authorization URL for you to open in a browser.
After granting permissions, paste the redirect URL back here to generate token.json

Usage:
    python authenticate_gmail.py
"""

import os
import sys
from urllib.parse import urlencode

# Allow insecure transport for local testing (required for http://localhost)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

try:
    from google_auth_oauthlib.flow import Flow
except ImportError:
    print("\n" + "!"*70)
    print("ERROR: Required library not installed")
    print("!"*70)
    print("\nPlease install required packages:")
    print("  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    print("\nOr install from requirements.txt:")
    print("  pip install -r requirements.txt")
    print("!"*70 + "\n")
    sys.exit(1)

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def main():
    print("\n" + "="*70)
    print("GMAIL API MANUAL AUTHENTICATION")
    print("="*70)

    # Check if credentials.json exists
    if not os.path.exists(CREDENTIALS_FILE):
        print("\n" + "!"*70)
        print("ERROR: credentials.json not found!")
        print("!"*70)
        print(f"\nExpected location: {CREDENTIALS_FILE}")
        print("\nPlease:")
        print("1. Go to Google Cloud Console")
        print("2. Create OAuth 2.0 credentials (Desktop app)")
        print("3. Download as credentials.json")
        print("4. Place in project root")
        print("\nSee docs/EMAIL_TESTING.md for details")
        print("!"*70 + "\n")
        sys.exit(1)

    print("\n✓ Found credentials.json")

    try:
        # Create the flow to get client config
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES
        )

        flow.redirect_uri = 'http://localhost'

        # Manually construct the auth URL to avoid double-encoding issues
        import secrets
        state = secrets.token_urlsafe(32)

        params = {
            'response_type': 'code',
            'client_id': flow.client_config['client_id'],
            'redirect_uri': flow.redirect_uri,
            'scope': ' '.join(SCOPES),
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }

        auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"

        print("\n" + "="*70)
        print("STEP 1: OPEN THIS URL IN YOUR BROWSER")
        print("="*70)
        print("\nCopy this ENTIRE URL and paste it in your browser:\n")
        print(auth_url)
        print("\n" + "="*70)
        print("STEP 2: GRANT PERMISSIONS")
        print("="*70)
        print("- Sign in to your Google account")
        print("- Click 'Continue' on ALL permission screens")
        print("- After granting permissions, you'll be redirected")
        print("")
        print("="*70)
        print("STEP 3: COPY THE REDIRECT URL")
        print("="*70)
        print("- Your browser will show 'Unable to connect' or similar")
        print("- THIS IS NORMAL - just copy the URL from the address bar")
        print("- The URL will look like:")
        print("  http://localhost/?state=...&code=...&scope=...")
        print("- Copy the ENTIRE URL")
        print("="*70 + "\n")

        # Get redirect URL from user
        redirect_url = input("Paste the full redirect URL here: ").strip()

        if not redirect_url:
            print("\n❌ No URL provided. Exiting.")
            sys.exit(1)

        if 'code=' not in redirect_url:
            print("\n❌ Invalid URL - must contain 'code=' parameter")
            print("Make sure you copied the entire URL from your browser's address bar")
            sys.exit(1)

        print("\n⏳ Extracting redirect URI from your URL...")

        # Extract the base redirect URI from the pasted URL
        from urllib.parse import urlparse
        parsed = urlparse(redirect_url)

        # Reconstruct the base URI (scheme + netloc + path without query)
        if parsed.path and parsed.path != '/':
            redirect_uri = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        else:
            redirect_uri = f"{parsed.scheme}://{parsed.netloc}"

        print(f"   Detected redirect URI: {redirect_uri}")
        print("⏳ Recreating flow with correct redirect URI...")

        # Recreate the flow with the correct redirect_uri
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )

        print("⏳ Exchanging code for tokens...")

        # Exchange the authorization response for credentials
        flow.fetch_token(authorization_response=redirect_url)
        creds = flow.credentials

        # Save the credentials to token.json
        print(f"⏳ Saving credentials to {TOKEN_FILE}...")
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        print("\n" + "="*70)
        print("✓✓✓ SUCCESS!")
        print("="*70)

        # Check for refresh token
        if creds.refresh_token:
            print("✓ Refresh token received - authentication will persist!")
        else:
            print("⚠ WARNING: No refresh token received")
            print("  You may need to re-authenticate later")

        print(f"\n✓ Token saved to: {TOKEN_FILE}")
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)
        print("1. Update your .env file:")
        print("   EMAIL_BACKEND=gmail_api")
        print("   DEFAULT_FROM_EMAIL=your-email@gmail.com")
        print("")
        print("2. Test the setup:")
        print("   python test_gmail.py")
        print("")
        print("3. Restart your Django server")
        print("="*70 + "\n")

    except Exception as e:
        print("\n" + "!"*70)
        print("ERROR: Authentication failed")
        print("!"*70)
        print(f"\n{str(e)}\n")

        if "invalid_grant" in str(e).lower():
            print("The authorization code has expired or was already used.")
            print("Run this script again to get a new authorization URL.")

        print("\nFor help, see docs/EMAIL_TESTING.md")
        print("!"*70 + "\n")
        sys.exit(1)

if __name__ == '__main__':
    main()

