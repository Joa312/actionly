# ACTIONLY API Testing

## DataForSEO Test Script
`python
import requests
import json

def test_dataforseo():
    api_key = "941a59a1725b4727"
    username = "nobis.intelligence@gmail.com"
    
    # Test Business Data API
    url = "https://api.dataforseo.com/v3/business_data/business_listings/search/live"
    
    headers = {
        'Authorization': f'Basic {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = [{
        "location_name": "Stockholm,Sweden",
        "categories": ["lodging"],
        "limit": 10
    }]
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

if __name__ == "__main__":
    result = test_dataforseo()
    print(json.dumps(result, indent=2))
`

## RapidAPI Hotel Data Test
`python
import requests

def test_rapidapi_hotels():
    url = "https://booking-com.p.rapidapi.com/v1/hotels/search"
    
    querystring = {
        "dest_id": "-2636528",  # Stockholm
        "order_by": "popularity",
        "filter_by_currency": "EUR",
        "checkin_date": "2025-07-14",
        "checkout_date": "2025-07-21",
        "adults_number": "2",
        "room_number": "1"
    }
    
    headers = {
        "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()
`

---
Created: 2025-07-08 12:01
