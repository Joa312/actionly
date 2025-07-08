import requests
import json

def debug_stockholm():
    api_key = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
    
    # Find Stockholm location
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    params = {"query": "Stockholm Sweden", "languageCode": "en"}
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "booking-com18.p.rapidapi.com"}
    
    print("Finding Stockholm...")
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print("Response structure:")
    print(json.dumps(data, indent=2)[:1000])
    
    # Try to find location data
    if 'data' in data and data['data']:
        first_result = data['data'][0]
        print("\nFirst result keys:")
        print(list(first_result.keys()))
        
        # Look for ID field
        for key in first_result.keys():
            if 'id' in key.lower() or 'location' in key.lower():
                print(f"Potential ID field: {key} = {first_result[key]}")

if __name__ == "__main__":
    debug_stockholm()
