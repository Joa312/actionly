# TEST STOCKHOLM HOTELS MED RAPIDAPI
import requests
import json

def test_stockholm_hotels():
    """Test RapidAPI med Stockholm hotell"""
    
    # Din RapidAPI nyckel
    api_key = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
    
    # Stockholm search
    url = "https://booking-com18.p.rapidapi.com/stays/search"
    
    # Stockholm location ID
    querystring = {
        "locationId": "eyJjaXR5X25hbWUiOiJTdG9ja2hvbG0iLCJjb3VudHJ5IjoiU3dlZGVuIiwiZGVzdF9pZCI6Ii0yNjM2NTI4IiwiZGVzdF90eXBlIjoiY2l0eSJ9",
        "units": "metric",
        "temperature": "c",
        "checkinDate": "2025-07-14",
        "checkoutDate": "2025-07-21",
        "adults": "2",
        "children": "0",
        "rooms": "1",
        "currency": "EUR"
    }
    
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "booking-com18.p.rapidapi.com"
    }
    
    print("🚀 Testing Stockholm Hotels with RapidAPI...")
    print("=" * 50)
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}...")
        
        if response.status_code == 200:
            print("✅ SUCCESS! API call worked!")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_stockholm_hotels()
