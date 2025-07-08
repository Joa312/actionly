import requests

def test_stockholm():
    api_key = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
    
    # Find Stockholm location
    url1 = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    params1 = {"query": "Stockholm Sweden", "languageCode": "en"}
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "booking-com18.p.rapidapi.com"}
    
    print("Finding Stockholm...")
    response1 = requests.get(url1, headers=headers, params=params1)
    data1 = response1.json()
    
    if response1.status_code == 200 and 'data' in data1:
        stockholm_id = data1['data'][0]['locationId']
        print(f"Found Stockholm: {data1['data'][0]['name']}")
        
        # Search hotels
        url2 = "https://booking-com18.p.rapidapi.com/stays/search"
        params2 = {
            "locationId": stockholm_id,
            "checkinDate": "2025-07-14",
            "checkoutDate": "2025-07-21",
            "adults": "2",
            "rooms": "1",
            "currency": "EUR"
        }
        
        response2 = requests.get(url2, headers=headers, params=params2)
        data2 = response2.json()
        
        if response2.status_code == 200:
            hotels = data2.get('data', [])[:5]
            print(f"\nFound {len(hotels)} Stockholm hotels:")
            
            for i, hotel in enumerate(hotels, 1):
                name = hotel.get('name', 'Unknown')
                price_data = hotel.get('priceBreakdown', {}).get('grossPrice', {})
                price = price_data.get('value', 'N/A')
                rating = hotel.get('reviewScore', 'N/A')
                
                print(f"{i}. {name}")
                print(f"   Price: {price} EUR")
                print(f"   Rating: {rating}/10")
                print("-" * 20)
        else:
            print(f"Hotel search failed: {response2.status_code}")
    else:
        print(f"Location search failed: {response1.status_code}")

if __name__ == "__main__":
    test_stockholm()
