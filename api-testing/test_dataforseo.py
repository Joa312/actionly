# DATAFORSEO API TEST - Stockholm Hotels
# Test your existing API key: 941a59a1725b4727

import requests
import json
from base64 import b64encode

def test_dataforseo_hotels():
    """Test DataForSEO Business API for Stockholm hotels"""
    
    # Your existing credentials
    username = "nobis.intelligence@gmail.com"
    password = "941a59a1725b4727"
    
    # Create authorization header
    credentials = f"{username}:{password}"
    encoded_credentials = b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }
    
    # Test Business Listings for Stockholm hotels
    url = "https://api.dataforseo.com/v3/business_data/business_listings/search/live"
    
    payload = [{
        "location_name": "Stockholm,Sweden",
        "categories": ["lodging"],  # Hotel category
        "limit": 20,  # Number of hotels
        "offset": 0,
        "language_code": "en",
        "order_by": ["rating.value,desc"],  # Best rated first
        
        # FILTERS WE CAN CONTROL:
        "filters": [
            ["rating.value", ">", 4.0],  # Only 4+ star hotels
            ["rating.votes_count", ">", 50]  # Hotels with many reviews
        ]
    }]
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        print("🏨 STOCKHOLM HOTELS TEST RESULTS:")
        print("=" * 50)
        
        if 'tasks' in data and data['tasks']:
            task = data['tasks'][0]
            
            if 'result' in task and task['result']:
                hotels = task['result']
                
                print(f"✅ Found {len(hotels)} hotels")
                print("\n📋 HOTEL DETAILS:\n")
                
                for i, hotel in enumerate(hotels[:5], 1):  # Show first 5
                    print(f"{i}. {hotel.get('title', 'Unknown Hotel')}")
                    print(f"   📍 Address: {hotel.get('address', 'N/A')}")
                    print(f"   ⭐ Rating: {hotel.get('rating', {}).get('value', 'N/A')}/5")
                    print(f"   📞 Phone: {hotel.get('phone', 'N/A')}")
                    print(f"   🌐 Website: {hotel.get('domain', 'N/A')}")
                    print(f"   💬 Reviews: {hotel.get('rating', {}).get('votes_count', 0)}")
                    
                    # GPS coordinates
                    cid = hotel.get('cid')
                    if cid:
                        print(f"   📍 GPS: Available (CID: {cid})")
                    print("-" * 30)
                    
            else:
                print("❌ No results found")
                print(f"Task status: {task.get('status_message', 'Unknown')}")
        else:
            print("❌ API call failed")
            print(f"Response: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_rapidapi_prices():
    """Example of what RapidAPI can give us for PRICES"""
    
    print("\n🏷️ RAPIDAPI BOOKING.COM EXAMPLE:")
    print("=" * 50)
    print("With RapidAPI we can get:")
    print("✅ Live room prices: €127/night")
    print("✅ Room types: Standard Double, Deluxe Suite")
    print("✅ Availability: Real-time for your dates")
    print("✅ Facilities: WiFi, Breakfast, Parking")
    print("✅ Photos: 15+ hotel images")
    print("✅ Direct booking: Link to Booking.com")
    print("\n💡 Need RapidAPI key for this data!")

if __name__ == "__main__":
    print("🚀 Testing ACTIONLY Data Sources...")
    print("Testing your existing DataForSEO API...")
    
    # Test DataForSEO
    test_dataforseo_hotels()
    
    # Show RapidAPI capabilities  
    test_rapidapi_prices()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run this script to test DataForSEO")
    print("2. Get RapidAPI key for live prices")
    print("3. Combine both for complete hotel data")