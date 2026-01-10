"""
Gmail API utility functions for sending emails.

Gmail no longer supports SMTP with app passwords for new applications.
This module provides Gmail API integration for sending emails.

Setup:
1. Enable Gmail API in Google Cloud Console
2. Create OAuth 2.0 credentials (Desktop app)
3. Download credentials.json to project root
4. Run authenticate_gmail() once to get token.json
5. Set EMAIL_BACKEND=gmail_api in your .env file

Token Storage:
- token.json is automatically created after first authentication
- Contains access token (1 hour lifetime) and refresh token (long-lived)
- System automatically refreshes expired access tokens using the refresh token
- You only need to authenticate ONCE - token.json persists across restarts
- Refresh token does not expire unless:
  * You revoke access in Google account settings
  * You delete token.json
  * The refresh token is unused for 6 months (Google's inactivity policy)

For detailed setup instructions, see docs/EMAIL_TESTING.md
"""

import base64
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from django.conf import settings


# Gmail API scopes - only need send permission
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Paths for credentials
CREDENTIALS_FILE = os.path.join(settings.BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(settings.BASE_DIR, 'token.json')


def authenticate_gmail():
    """
    Authenticate with Gmail API and save credentials.

    This should be run once to generate token.json.
    Opens a browser window for OAuth consent.

    Returns:
        service: Gmail API service object
    """
    creds = None

    # Check if we have a token file
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print(f"Credentials refreshed and saved to {TOKEN_FILE}")
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                print("Will need to re-authenticate...")
                # Delete invalid token and re-authenticate
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Credentials file not found: {CREDENTIALS_FILE}\n"
                    "Please download OAuth credentials from Google Cloud Console.\n"
                    "See docs/EMAIL_TESTING.md for setup instructions."
                )

            print("\n" + "="*70)
            print("GMAIL API AUTHENTICATION")
            print("="*70)
            print("IMPORTANT: Complete ALL permission screens to get refresh token!")
            print("="*70 + "\n")

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

            # Try to use local server first, fallback to manual flow if it fails
            try:
                print("Attempting automatic authentication with local server...")
                # Request offline access to get refresh token, and force consent screen
                creds = flow.run_local_server(
                    port=0,
                    access_type='offline',
                    prompt='consent',
                    open_browser=True
                )
                print("\n✓ Automatic authentication successful!")
            except Exception as e:
                print(f"\nAutomatic method failed: {e}")
                print("\nSwitching to MANUAL authentication mode...")
                print("-"*70)

                # Recreate flow for manual method
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

                # Generate authorization URL
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    prompt='consent'
                )

                print("\n1. Open this URL in your browser:")
                print(f"\n{auth_url}\n")
                print("2. Sign in and grant ALL permissions")
                print("3. After authorization, you'll be redirected to a URL")
                print("4. Copy the ENTIRE URL from your browser's address bar")
                print("   (It will start with http://localhost and contain 'code=')")
                print("5. Paste it below:\n")

                redirect_response = input("Paste the full redirect URL here: ").strip()

                # Extract code from URL
                if 'code=' not in redirect_response:
                    raise ValueError("Invalid redirect URL - must contain 'code=' parameter")

                # Fetch token using the redirect response
                flow.fetch_token(authorization_response=redirect_response)
                creds = flow.credentials
                print("\n✓ Manual authentication successful!")

            # Save credentials for next run
            print(f"\nSaving credentials to {TOKEN_FILE}...")
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print(f"✓ Credentials saved to {TOKEN_FILE}")

            # Verify refresh token was received
            if not creds.refresh_token:
                print("\n" + "!"*70)
                print("WARNING: No refresh token received!")
                print("!"*70)
                print("You may need to re-authenticate each time.")
                print("To fix: Delete token.json and ensure you grant ALL permissions.")
            else:
                print("\n" + "="*70)
                print("✓✓✓ SUCCESS! Refresh token received!")
                print("="*70)
                print("Authentication will persist - no need to log in again!")
                print("="*70 + "\n")

    return build('gmail', 'v1', credentials=creds)


def get_gmail_service():
    """
    Get authenticated Gmail API service.

    Returns:
        service: Gmail API service object

    Raises:
        Exception: If authentication fails
    """
    try:
        return authenticate_gmail()
    except Exception as e:
        raise Exception(
            f"Failed to authenticate with Gmail API: {e}\n"
            "Run 'python manage.py shell' and execute:\n"
            "  from cart.gmail_utils import authenticate_gmail\n"
            "  authenticate_gmail()\n"
            "See docs/EMAIL_TESTING.md for setup instructions."
        )


def send_email_via_gmail_api(subject, body, to_addresses, from_email=None):
    """
    Send email using Gmail API.

    Args:
        subject: Email subject line
        body: Email body (plain text)
        to_addresses: List of recipient email addresses
        from_email: Sender email (optional, uses settings.DEFAULT_FROM_EMAIL)

    Returns:
        dict: Response from Gmail API

    Raises:
        Exception: If sending fails
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        service = get_gmail_service()

        # Create message
        message = MIMEText(body)
        message['to'] = ', '.join(to_addresses)
        message['from'] = from_email
        message['subject'] = subject

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send message
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        print(f"Email sent successfully. Message ID: {send_message['id']}")
        return send_message

    except HttpError as error:
        raise Exception(f"Gmail API error: {error}")
    except Exception as error:
        raise Exception(f"Failed to send email: {error}")


def send_html_email_via_gmail_api(subject, text_body, html_body, to_addresses, from_email=None):
    """
    Send HTML email using Gmail API.

    Args:
        subject: Email subject line
        text_body: Plain text version of email
        html_body: HTML version of email
        to_addresses: List of recipient email addresses
        from_email: Sender email (optional, uses settings.DEFAULT_FROM_EMAIL)

    Returns:
        dict: Response from Gmail API

    Raises:
        Exception: If sending fails
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        service = get_gmail_service()

        # Create multipart message
        message = MIMEMultipart('alternative')
        message['to'] = ', '.join(to_addresses)
        message['from'] = from_email
        message['subject'] = subject

        # Attach both plain text and HTML versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        message.attach(part1)
        message.attach(part2)

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send message
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        print(f"HTML email sent successfully. Message ID: {send_message['id']}")
        return send_message

    except HttpError as error:
        raise Exception(f"Gmail API error: {error}")
    except Exception as error:
        raise Exception(f"Failed to send email: {error}")


# Django email backend compatible wrapper
def send_mail_gmail_api(subject, message, from_email, recipient_list, fail_silently=False):
    """
    Django-compatible send_mail function using Gmail API.

    This function mimics django.core.mail.send_mail() but uses Gmail API.

    Args:
        subject: Email subject
        message: Email body (plain text)
        from_email: Sender email address
        recipient_list: List of recipient email addresses
        fail_silently: If True, don't raise exceptions on errors

    Returns:
        int: Number of successfully sent emails (0 or 1)
    """
    try:
        send_email_via_gmail_api(subject, message, recipient_list, from_email)
        return 1
    except Exception as e:
        if not fail_silently:
            raise
        print(f"Failed to send email: {e}")
        return 0

