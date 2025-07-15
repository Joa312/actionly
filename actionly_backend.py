def get_hotels_com_region_id_fixed(city_name):
    """Get Hotels.com region ID using CORRECT locations/search endpoint"""
    url = "https://hotels4.p.rapidapi.com/locations/search"
    
    querystring = {
        "query": city_name,
        "locale": "en_US"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_HOTELS
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"🔍 Hotels.com locations/search response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Response data keys: {list(data.keys()) if data else 'None'}")
            
            # Look for suggestions array (common in Hotels.com API)
            if 'suggestions' in data:
                for suggestion in data['suggestions']:
                    if suggestion.get('group') == 'CITY_GROUP':
                        entities = suggestion.get('entities', [])
                        for entity in entities:
                            if entity.get('type') == 'CITY':
                                destination_id = entity.get('destinationId')
                                if destination_id:
                                    return destination_id
                                    
            # Alternative: look for sr array (similar to v3 structure)
            if 'sr' in data:
                for location in data['sr']:
                    if location.get('type') == 'CITY' and location.get('gaiaId'):
                        return location['gaiaId']
                        
            # Another alternative: direct destinationId in results
            if isinstance(data, dict) and 'destinationId' in data:
                return data['destinationId']
                
            # Last resort: any ID we can find
            if isinstance(data, list) and data:
                for item in data:
                    if isinstance(item, dict):
                        for key in ['destinationId', 'gaiaId', 'id']:
                            if key in item:
                                return item[key]
                                
        else:
            print(f"❌ Hotels.com API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error getting Hotels.com region ID: {e}")
    
    return None

def search_hotels_com_api_fixed(destination_id, checkin, checkout, adults):
    """Search hotels using Hotels.com API with correct structure"""
    url = "https://hotels4.p.rapidapi.com/properties/list"
    
    querystring = {
        "destinationId": destination_id,
        "pageNumber": 1,
        "pageSize": 25,
        "checkIn": checkin,
        "checkOut": checkout,
        "adults1": adults,
        "sortOrder": "PRICE",
        "locale": "en_US",
        "currency": "USD"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_HOTELS
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"🔍 Hotels.com properties/list response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data
            
    except Exception as e:
        print(f"Error searching Hotels.com: {e}")
    
    return None

@app.route('/debug-hotels-com-fixed')
def debug_hotels_com_fixed():
    """Fixed Hotels.com debug with correct endpoints"""
    city = 'Stockholm'
    checkin = '2025-07-15'
    checkout = '2025-07-16'
    adults = 2
    
    debug_info = {
        'fix_applied': 'Using locations/search instead of locations/v3/search',
        'research_source': 'Hotels.com API discussions on RapidAPI',
        'test_parameters': {
            'city': city,
            'checkin': checkin,
            'checkout': checkout,
            'adults': adults
        }
    }
    
    # Step 1: Get destination ID using CORRECT endpoint
    print(f"🔍 Step 1: Getting Hotels.com destination ID for {city}")
    destination_id = get_hotels_com_region_id_fixed(city)
    
    debug_info['step_1_location_search'] = {
        'endpoint': 'locations/search (FIXED)',
        'city_searched': city,
        'destination_id_found': destination_id,
        'success': destination_id is not None
    }
    
    if not destination_id:
        debug_info['final_analysis'] = {
            'overall_success': False,
            'step1_success': False,
            'step2_success': False,
            'hotels_found': 0,
            'error': 'Could not find destination ID for Stockholm using fixed endpoint'
        }
        return jsonify(debug_info)
    
    # Step 2: Search hotels using properties/list endpoint
    print(f"🔍 Step 2: Searching hotels with destination ID {destination_id}")
    hotels_data = search_hotels_com_api_fixed(destination_id, checkin, checkout, adults)
    
    debug_info['step_2_hotels_search'] = {
        'endpoint': 'properties/list',
        'method': 'GET with querystring',
        'destination_id_used': destination_id,
        'response_received': hotels_data is not None,
        'success': hotels_data is not None
    }
    
    if hotels_data:
        # Extract hotels from response
        hotels = []
        if 'data' in hotels_data and 'body' in hotels_data['data']:
            search_results = hotels_data['data']['body'].get('searchResults', {})
            results = search_results.get('results', [])
            hotels = results[:10]  # Limit to 10 for debug
            
            debug_info['step_2_hotels_search']['hotels_found'] = len(hotels)
            debug_info['step_2_hotels_search']['sample_hotels'] = [
                {
                    'name': hotel.get('name', 'N/A'),
                    'id': hotel.get('id', 'N/A'),
                    'price': hotel.get('ratePlan', {}).get('price', {}).get('current', 'N/A')
                } for hotel in hotels[:3]
            ]
        
        debug_info['final_analysis'] = {
            'overall_success': len(hotels) > 0,
            'step1_success': True,
            'step2_success': True,
            'hotels_found': len(hotels),
            'fix_worked': len(hotels) > 0
        }
    else:
        debug_info['final_analysis'] = {
            'overall_success': False,
            'step1_success': True,
            'step2_success': False,
            'hotels_found': 0,
            'error': 'Hotels search returned null despite valid destination ID'
        }
    
    return jsonify(debug_info)
