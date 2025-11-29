#!/usr/bin/env python3
"""
Quick test script - run this locally first to verify the API works.
Usage: python scripts/test_api.py
"""

import requests
import json

API_URL = "https://apps.myclearwater.com/activecalls/api/ActiveCalls"

def test_api():
    print("Testing CPD Active Calls API...")
    print(f"URL: {API_URL}")
    print("-" * 60)
    
    try:
        response = requests.get(API_URL, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict) and 'data' in data:
                calls = data['data']
            elif isinstance(data, list):
                calls = data
            else:
                print(f"Unexpected format: {type(data)}")
                print(json.dumps(data, indent=2)[:1000])
                return
            
            print(f"\n✅ SUCCESS! Found {len(calls)} active calls\n")
            
            if calls:
                print("Sample call structure:")
                print(json.dumps(calls[0], indent=2))
                
                print("\n" + "=" * 60)
                print("ALL CURRENT ACTIVE CALLS:")
                print("=" * 60)
                
                for call in calls:
                    incident = call.get('Master_Incident_Number', 'N/A')
                    desc = call.get('Online_Description', 'N/A')
                    addr = call.get('Address', 'N/A')
                    time = call.get('Response_Date', 'N/A')
                    
                    print(f"\n[{incident}]")
                    print(f"  Type: {desc}")
                    print(f"  Location: {addr}")
                    print(f"  Time: {time}")
            else:
                print("No active calls at this time (or format different than expected)")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(response.text[:500])
            
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Raw response: {response.text[:500]}")


if __name__ == "__main__":
    test_api()
