#!/usr/bin/env python3
"""
Google Ads API - Refresh Token Generator

This script helps you generate a refresh token for Google Ads API.
Run this once to get your refresh token, then add it to your .env file.
"""

from google_auth_oauthlib.flow import InstalledAppFlow

# OAuth2 scope for Google Ads API
SCOPES = ['https://www.googleapis.com/auth/adwords']

def main():
    print("\n" + "="*60)
    print("Google Ads API - Refresh Token Generator")
    print("="*60 + "\n")

    # Get Client ID and Client Secret from user
    print("First, you need your OAuth2 credentials from Google Cloud Console")
    print("(APIs & Services → Credentials → OAuth 2.0 Client IDs)\n")

    client_id = input("Enter your Client ID: ").strip()
    client_secret = input("Enter your Client Secret: ").strip()

    if not client_id or not client_secret:
        print("\n❌ Error: Client ID and Client Secret are required!")
        return

    print("\n🔄 Starting OAuth2 flow...\n")

    # Create OAuth2 flow
    flow = InstalledAppFlow.from_client_config(
        client_config={
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        },
        scopes=SCOPES
    )

    # Run the OAuth2 flow
    try:
        credentials = flow.run_local_server(port=0)

        print("\n" + "="*60)
        print("✅ SUCCESS! Your refresh token:")
        print("="*60)
        print(f"\n{credentials.refresh_token}\n")
        print("="*60)

        print("\n📝 Next steps:")
        print("1. Copy the refresh token above")
        print("2. Add it to your backend/.env file as GOOGLE_ADS_REFRESH_TOKEN")
        print("3. Also add your Client ID and Client Secret to .env")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error during OAuth flow: {e}")
        print("\nMake sure:")
        print("1. Your Client ID and Client Secret are correct")
        print("2. You've enabled Google Ads API in your project")
        print("3. The OAuth consent screen is configured")

if __name__ == "__main__":
    main()
