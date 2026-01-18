#!/usr/bin/env python3
"""
Test Google Ads API Connection

This script verifies that your Google Ads API credentials are working correctly.
"""

import os
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Load environment variables
load_dotenv()

def test_connection():
    print("\n" + "="*60)
    print("Testing Google Ads API Connection")
    print("="*60 + "\n")

    # Check if credentials are set
    required_vars = [
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'GOOGLE_ADS_CLIENT_ID',
        'GOOGLE_ADS_CLIENT_SECRET',
        'GOOGLE_ADS_REFRESH_TOKEN',
        'GOOGLE_ADS_LOGIN_CUSTOMER_ID',
        'GOOGLE_ADS_CUSTOMER_ID'
    ]

    print("1. Checking environment variables...")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your-'):
            missing_vars.append(var)
            print(f"   ❌ {var}: Not set or using placeholder")
        else:
            # Mask sensitive values
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"   ✅ {var}: {masked}")

    if missing_vars:
        print(f"\n❌ Missing or placeholder values for: {', '.join(missing_vars)}")
        print("\nPlease update your .env file with real credentials.")
        return False

    print("\n2. Testing Google Ads API connection...")

    try:
        # Initialize Google Ads client
        credentials = {
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
            "use_proto_plus": True
        }

        client = GoogleAdsClient.load_from_dict(credentials)
        customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")

        # Try to get customer information
        customer_service = client.get_service("CustomerService")
        customer_resource_name = customer_service.customer_path(customer_id)

        ga_service = client.get_service("GoogleAdsService")
        query = f"""
            SELECT
                customer.id,
                customer.descriptive_name,
                customer.currency_code,
                customer.time_zone
            FROM customer
            WHERE customer.resource_name = '{customer_resource_name}'
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            customer = row.customer
            print(f"\n   ✅ Successfully connected to Google Ads!")
            print(f"\n   Account Details:")
            print(f"   - Customer ID: {customer.id}")
            print(f"   - Name: {customer.descriptive_name}")
            print(f"   - Currency: {customer.currency_code}")
            print(f"   - Time Zone: {customer.time_zone}")

        print("\n" + "="*60)
        print("✅ Google Ads API connection successful!")
        print("="*60 + "\n")
        return True

    except GoogleAdsException as ex:
        print(f"\n   ❌ Google Ads API Error:")
        print(f"   Request ID: {ex.request_id}")
        print(f"   Status: {ex.error.code().name}")

        for error in ex.failure.errors:
            print(f"\n   Error Message: {error.message}")
            if error.location:
                for field in error.location.field_path_elements:
                    print(f"   Field: {field.field_name}")

        print("\n💡 Common issues:")
        print("   - Developer token not approved (apply in Google Ads)")
        print("   - Wrong customer ID (check format: 1234567890, no dashes)")
        print("   - Refresh token expired (regenerate using generate_refresh_token.py)")
        print("   - API not enabled in Google Cloud Console")

        return False

    except Exception as ex:
        print(f"\n   ❌ Unexpected error: {ex}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
