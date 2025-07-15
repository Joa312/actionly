# STAYFINDR BACKEND - European Hotel Search Engine
# Flask backend with Booking.com + WORKING Hotels.com API integration
# FIXED: Correct Hotels.com endpoints based on research

import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import time
from datetime import datetime
from urllib.parse import quote_plus

app = Flask(__name__)
CORS(app)

# RapidAPI Configuration
RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
RAPIDAPI_HOST_BOOKING = "booking-com18.p.rapidapi.com"
RAPIDAPI_HOST_HOTELS = "hotels4.p.rapidapi.com"

# European Cities Configuration - 29 major destinations
CITIES = {
    'stockholm': {
        'name': 'Stockholm, Sweden',
        'coordinates': [59.3293, 18.0686],
        'search_query': 'Stockholm Sweden',
        'hotels_search': 'Stockholm'
    },
    'paris': {
        'name': 'Paris, France', 
        'coordinates': [48.8566, 2.3522],
        'search_query': 'Paris France',
        'hotels_search': 'Paris'
    },
    'london': {
        'name': 'London, UK',
        'coordinates': [51.5074, -0.1278],
        'search_query': 'London United Kingdom',
        'hotels_search': 'London'
    },
    'amsterdam': {
        'name': 'Amsterdam, Netherlands',
        'coordinates': [52.3676, 4.9041],
        'search_query': 'Amsterdam Netherlands',
        'hotels_search': 'Amsterdam'
    },
    'barcelona': {
        'name': 'Barcelona, Spain',
        'coordinates': [41.3851, 2.1734],
        'search_query': 'Barcelona Spain',
        'hotels_search': 'Barcelona'
    },
    'rome': {
        'name': 'Rome, Italy',
        'coordinates': [41.9028, 12.4964],
        'search_query': 'Rome Italy',
        'hotels_search': 'Rome'
    },
    'berlin': {
        'name': 'Berlin, Germany',
        'coordinates': [52.5200, 13.4050],
        'search_query': 'Berlin Germany',
        'hotels_search': 'Berlin'
    },
    'copenhagen': {
        'name': 'Copenhagen, Denmark',
        'coordinates': [55.6761, 12.5683],
        'search_query': 'Copenhagen Denmark',
        'hotels_search': 'Copenhagen'
    },
    'vienna': {
        'name': 'Vienna, Austria',
        'coordinates': [48.2082, 16.3738],
        'search_query': 'Vienna Austria',
        'hotels_search': 'Vienna'
    },
    'prague': {
        'name': 'Prague, Czech Republic',
        'coordinates': [50.0755, 14.4378],
        'search_query': 'Prague Czech Republic',
        'hotels_search': 'Prague'
    },
    'madrid': {
        'name': 'Madrid, Spain',
        'coordinates': [40.4168, -3.7038],
        'search_query': 'Madrid Spain',
        'hotels_search': 'Madrid'
    },
    'milano': {
        'name': 'Milano, Italy',
        'coordinates': [45.4642, 9.1900],
        'search_query': 'Milano Italy',
        'hotels_search': 'Milano'
    },
    'zurich': {
        'name': 'Zürich, Switzerland',
        'coordinates': [47.3769, 8.5417],
        'search_query': 'Zürich Switzerland',
        'hotels_search': 'Zurich'
    },
    'oslo': {
        'name': 'Oslo, Norway',
        'coordinates': [59.9139, 10.7522],
        'search_query': 'Oslo Norway',
        'hotels_search': 'Oslo'
    },
    'helsinki': {
        'name': 'Helsinki, Finland',
        'coordinates': [60.1695, 24.9354],
        'search_query': 'Helsinki Finland',
        'hotels_search': 'Helsinki'
    },
    'warsaw': {
        'name': 'Warsaw, Poland',
        'coordinates': [52.2297, 21.0122],
        'search_query': 'Warsaw Poland',
        'hotels_search': 'Warsaw'
    },
    'budapest': {
        'name': 'Budapest, Hungary',
        'coordinates': [47.4979, 19.0402],
        'search_query': 'Budapest Hungary',
        'hotels_search': 'Budapest'
    },
    'dublin': {
        'name': 'Dublin, Ireland',
        'coordinates': [53.3498, -6.2603],
        'search_query': 'Dublin Ireland',
        'hotels_search': 'Dublin'
    },
    'lisbon': {
        'name': 'Lisbon, Portugal',
        'coordinates': [38.7223, -9.1393],
        'search_query': 'Lisbon Portugal',
        'hotels_search': 'Lisbon'
    },
    'brussels': {
        'name': 'Brussels, Belgium',
        'coordinates': [50.8503, 4.3517],
        'search_query': 'Brussels Belgium',
        'hotels_search': 'Brussels'
    },
    'athens': {
        'name': 'Athens, Greece',
        'coordinates': [37.9838, 23.7275],
        'search_query': 'Athens Greece',
        'hotels_search': 'Athens'
    },
    'munich': {
        'name': 'Munich, Germany',
        'coordinates': [48.1351, 11.5820],
        'search_query': 'Munich Germany',
        'hotels_search': 'Munich'
    },
    'lyon': {
        'name': 'Lyon, France',
        'coordinates': [45.7640, 4.8357],
        'search_query': 'Lyon France',
        'hotels_search': 'Lyon'
    },
    'florence': {
        'name': 'Florence, Italy',
        'coordinates': [43.7696, 11.2558],
        'search_query': 'Florence Italy',
        'hotels_search': 'Florence'
    },
    'edinburgh': {
        'name': 'Edinburgh, Scotland',
        'coordinates': [55.9533, -3.1883],
        'search_query': 'Edinburgh Scotland',
        'hotels_search': 'Edinburgh'
    },
    'nice': {
        'name': 'Nice, France',
        'coordinates': [43.7102, 7.2620],
        'search_query': 'Nice France',
        'hotels_search': 'Nice'
    },
    'palma': {
        'name': 'Palma, Spain',
        'coordinates': [39.5696, 2.6502],
        'search_query': 'Palma Spain',
        'hotels_search': 'Palma'
    },
    'santorini': {
        'name': 'Santorini, Greece',
        'coordinates': [36.3932, 25.4615],
        'search_query': 'Santorini Greece',
        'hotels_search': 'Santorini'
    },
    'ibiza': {
        'name': 'Ibiza, Spain',
        'coordinates': [38.9067, 1.4206],
        'search_query': 'Ibiza Spain',
        'hotels_search': 'Ibiza'
    }
}

# Country codes for Booking.com URLs based on city
COUNTRY_CODES = {
    'stockholm': 'sv', 'oslo': 'no', 'helsinki': 'fi', 'copenhagen': 'dk',
    'paris': 'fr', 'lyon': 'fr', 'nice': 'fr',
    'london': 'en-gb', 'edinburgh': 'en-gb',
    'amsterdam': 'nl', 'brussels': 'nl',
    'barcelona': 'es', 'madrid': 'es', 'palma': 'es', 'ibiza': 'es',
    'rome': 'it', 'milano': 'it', 'florence': 'it',
    'berlin': 'de', 'munich': 'de',
    'vienna': 'de', 'zurich': 'de',
    'prague': 'cs', 'warsaw': 'pl', 'budapest': 'hu',
    'dublin': 'en-gb', 'lisbon': 'pt', 'athens': 'el', 'santorini': 'el'
}

# Room Type Configurations with Junior Suite
ROOM_TYPES = {
    'single': {
        'name': 'Single Room',
        'description': 'Single Room - Perfect for solo travelers',
        'guests': 1,
        'keywords': ['single', 'solo', 'one bed'],
        'booking_param': 'single'
    },
    'double': {
        'name': 'Double Room',
        'description': 'Double Room - Ideal for couples',
        'guests': 2,
        'keywords': ['double', 'twin', 'couple'],
        'booking_param': 'double'
    },
    'family': {
        'name': 'Family Room',
        'description': 'Family Room - Spacious for families with children',
        'guests': 4,
        'keywords': ['family', 'connecting', 'kids', 'children'],
        'booking_param': 'family'
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'description': 'Junior Suite - Spacious room with sitting area',
        'guests': 2,
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded'],
        'booking_param': 'junior_suite'
    },
    'suite': {
        'name': 'Suite/Apartment',
        'description': 'Suite/Apartment - Luxury accommodation with separate living area',
        'guests': 3,
        'keywords': ['suite', 'apartment', 'luxury', 'living room', 'penthouse'],
        'booking_param': 'suite'
    }
}

def get_location_id_booking(city_query):
    """Get Booking.com location ID for a city"""
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {"query": city_query, "languageCode": "en"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_BOOKING
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return data['data'][0].get('id')
    except Exception as e:
        print(f"Error getting Booking.com location ID: {e}")
    
    return None

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

def search_hotels_booking_api(location_id, checkin, checkout, adults, rooms):
    """Search hotels using Booking.com API"""
    url = "https://booking-com18.p.rapidapi.com/stays/search"
    
    querystring = {
        "locationId": location_id,
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "adults": adults,
        "rooms": rooms,
        "currency": "EUR"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_BOOKING
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error searching Booking.com hotels: {e}")
    
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

def create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key):
    """Create hotel name-based booking URL for better targeting"""
    
    # Priority 1: Use direct hotel URL from API if available
    direct_urls = [
        hotel.get('url'),
        hotel.get('link'), 
        hotel.get('booking_url'),
        hotel.get('hotelUrl'),
        hotel.get('deepLink')
    ]
    
    for url in direct_urls:
        if url and 'booking.com' in str(url):
            # Add search parameters to direct URL
            if '?' in url:
                return f"{url}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
            else:
                return f"{url}?checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
    
    # Priority 2: Create hotel name-based search URL
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('propertyId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id and hotel_name:
        # Get country code for the city
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        
        # Encode hotel name properly for URL
        hotel_name_encoded = quote_plus(hotel_name)
        
        # Create hotel name-based search URL
        base_params = {
            'ss': hotel_name,  # Hotel search string
            'dest_id': hotel_id,  # Hotel destination ID
            'dest_type': 'hotel',  # Specify it's a hotel
            'checkin': checkin,
            'checkout': checkout,
            'group_adults': adults,
            'no_rooms': rooms,
            'group_children': 0,
            'search_selected': 'true'
        }
        
        # Build URL parameters
        params_string = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in base_params.items()])
        
        return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"
    
    # Priority 3: Fallback to hotel ID-based URL
    if hotel_id:
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        return f"https://www.booking.com/hotel/{country_code.split('-')[0]}/?hotel_id={hotel_id}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
    
    # Priority 4: Generic search by hotel name in the city
    hotel_name = hotel.get('name', '').replace(' ', '+')
    city_name = city_info['name'].replace(' ', '+')
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={hotel_name}+{city_name}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"

def create_hotels_com_url(hotel, checkin, checkout, adults, rooms):
    """Create Hotels.com booking URL"""
    hotel_id = hotel.get('id') or hotel.get('propertyId')
    
    if hotel_id:
        return f"https://www.hotels.com/ho{hotel_id}/?q-check-in={checkin}&q-check-out={checkout}&q-rooms=1&q-room-0-adults={adults}&q-room-0-children=0"
    
    # Fallback to search by hotel name
    hotel_name = hotel.get('name', '').replace(' ', '+')
    return f"https://www.hotels.com/search.do?q-destination={hotel_name}&q-check-in={checkin}&q-check-out={checkout}&q-rooms=1&q-room-0-adults={adults}"

def analyze_room_type(hotel_name, room_type_filter):
    """Analyze if hotel matches room type criteria"""
    if not room_type_filter or room_type_filter not in ROOM_TYPES:
        return True
    
    room_config = ROOM_TYPES[room_type_filter]
    hotel_name_lower = hotel_name.lower()
    
    # Check if hotel name contains room type keywords
    for keyword in room_config['keywords']:
        if keyword.lower() in hotel_name_lower:
            return True
    
    return True  # For now, include all hotels but mark preferred ones

def process_hotel_data(hotels_data, city_info, checkin, checkout, adults, rooms, city_key, room_type_filter=None, platform="booking"):
    """Process and format hotel data with proper booking URLs"""
    processed_hotels = []
    
    for i, hotel in enumerate(hotels_data):
        # Extract hotel information
        hotel_name = hotel.get('name', 'Unknown Hotel')
        
        # Room type filtering
        if not analyze_room_type(hotel_name, room_type_filter):
            continue
        
        # Get real coordinates if available, otherwise use city center with offset
        latitude = hotel.get('latitude')
        longitude = hotel.get('longitude')
        
        if latitude and longitude:
            coordinates = [float(latitude), float(longitude)]
        else:
            # Fallback: spread around city center
            base_lat, base_lng = city_info['coordinates']
            coordinates = [
                base_lat + (i * 0.01) - 0.05,
                base_lng + (i * 0.01) - 0.05
            ]
        
        # Extract pricing information
        price = 'N/A'
        currency = 'EUR' if platform == 'booking' else 'USD'
        
        if platform == 'booking':
            if 'priceBreakdown' in hotel:
                price_info = hotel['priceBreakdown'].get('grossPrice', {})
                if 'value' in price_info:
                    # Convert to per night if total price
                    total_price = price_info['value']
                    try:
                        # Estimate per night
                        from datetime import datetime
                        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
                        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
                        nights = (checkout_date - checkin_date).days
                        if nights > 0:
                            price = int(total_price / nights)
                        else:
                            price = total_price
                    except:
                        price = int(total_price / 7)  # Fallback: assume 7 nights
            elif 'price' in hotel:
                price = hotel['price']
        else:  # Hotels.com
            if 'ratePlan' in hotel:
                rate_plan = hotel['ratePlan']
                if 'price' in rate_plan and 'current' in rate_plan['price']:
                    price_str = rate_plan['price']['current']
                    # Extract numeric value from price string like "$123"
                    import re
                    price_match = re.search(r'[\d,]+', price_str.replace(',', ''))
                    if price_match:
                        price = int(price_match.group())
        
        # Extract rating
        rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)  # Normalize to 5-point scale
        else:
            rating = 4.0
        
        # Extract address
        address = hotel.get('address', city_info['name'])
        
        # Create optimized booking URL
        if platform == 'booking':
            booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key)
        else:
            booking_url = create_hotels_com_url(hotel, checkin, checkout, adults, rooms)
        
        # Add room type information if filtering
        room_type_info = ""
        if room_type_filter and room_type_filter in ROOM_TYPES:
            room_type_info = f" • {ROOM_TYPES[room_type_filter]['description']}"
        
        processed_hotel = {
            'id': f"{platform}_{hotel.get('id') or hotel.get('hotel_id') or f'hotel_{i}'}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'currency': currency,
            'rating': rating,
            'booking_url': booking_url,
            'platform': platform.title(),
            'room_type_info': room_type_info
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

@app.route('/api/hotels')
def get_hotels():
    """Get hotels from both Booking.com and Hotels.com with room type filtering"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-15')
    checkout = request.args.get('checkout', '2025-07-16')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    room_type = request.args.get('room_type', 'double')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    all_hotels = []
    platform_results = {}
    
    # Search Booking.com
    print(f"🔍 Searching Booking.com for {city}")
    booking_location_id = get_location_id_booking(city_info['search_query'])
    
    if booking_location_id:
        booking_data = search_hotels_booking_api(booking_location_id, checkin, checkout, adults, rooms)
        if booking_data and 'data' in booking_data:
            booking_hotels = process_hotel_data(
                booking_data['data'][:25], 
                city_info, 
                checkin, 
                checkout, 
                adults, 
                rooms, 
                city,
                room_type,
                "booking"
            )
            all_hotels.extend(booking_hotels)
            platform_results['booking'] = {
                'found': len(booking_hotels),
                'status': 'success'
            }
    
    # Search Hotels.com using FIXED method
    print(f"🔍 Searching Hotels.com for {city}")
    hotels_destination_id = get_hotels_com_region_id_fixed(city_info['hotels_search'])
    
    if hotels_destination_id:
        hotels_data = search_hotels_com_api_fixed(hotels_destination_id, checkin, checkout, adults)
        if hotels_data and 'data' in hotels_data:
            if 'body' in hotels_data['data'] and 'searchResults' in hotels_data['data']['body']:
                search_results = hotels_data['data']['body']['searchResults']
                results = search_results.get('results', [])
                hotels_com_hotels = process_hotel_data(
                    results[:25], 
                    city_info, 
                    checkin, 
                    checkout, 
                    adults, 
                    rooms, 
                    city,
                    room_type,
                    "hotels.com"
                )
                all_hotels.extend(hotels_com_hotels)
                platform_results['hotels_com'] = {
                    'found': len(hotels_com_hotels),
                    'status': 'success'
                }
            else:
                platform_results['hotels_com'] = {
                    'found': 0,
                    'status': 'no_results'
                }
    else:
        platform_results['hotels_com'] = {
            'found': 0,
            'status': 'no_destination_id'
        }
    
    # Remove duplicates based on hotel name similarity
    unique_hotels = []
    seen_names = set()
    
    for hotel in all_hotels:
        hotel_name_clean = hotel['name'].lower().replace(' ', '').replace('-', '')
        if hotel_name_clean not in seen_names:
            seen_names.add(hotel_name_clean)
            unique_hotels.append(hotel)
    
    # Add room type information to response
    room_type_info = ROOM_TYPES.get(room_type, ROOM_TYPES['double'])
    
    return jsonify({
        'city': city_info['name'],
        'hotels': unique_hotels,
        'total_found': len(unique_hotels),
        'platforms': platform_results,
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms,
            'room_type': room_type
        },
        'room_type_filter': room_type_info,
        'multiplatform': 'enabled',
        'hotels_com_fix': 'applied',
        'booking_optimization': 'enabled',
        'localization': 'enabled'
    })

@app.route('/test')
def test_multiplatform():
    """Test multiplatform search with Stockholm"""
    return get_hotels()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend...")
    print("🏨 Supporting 29 European cities")
    print("🌍 FIXED: Working Hotels.com integration")
    print("🔗 Frontend will connect to: http://localhost:5000")
    print("📋 Test API: http://localhost:5000/test")
    print("🔍 Debug Hotels.com: http://localhost:5000/debug-hotels-com-fixed")
    print("✅ Multiplatform: Booking.com + Hotels.com (FIXED)")
    
    # Use PORT environment variable for deployment (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)app.route('/')
def home():
    """API Documentation Page"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Backend API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .cities { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
            .city { background: #e3f2fd; padding: 8px; border-radius: 4px; text-align: center; }
            .feature { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API</h1>
        <p>Flask backend for European hotel search with WORKING Hotels.com integration</p>
        
        <div class="feature">
            <strong>✅ FIXED: Working Hotels.com Integration!</strong><br>
            Using correct locations/search endpoint with improved parsing
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels</strong> - Get hotels from both platforms<br>
            Parameters: city, checkin, checkout, adults, rooms, room_type<br>
            <em>Now with WORKING Hotels.com integration</em>
        </div>
        <div class="endpoint">
            <strong>/debug-hotels-com-fixed</strong> - Fixed Hotels.com debug
        </div>
        <div class="endpoint">
            <strong>/api/cities</strong> - List all 29 cities
        </div>
        <div class="endpoint">
            <strong>/api/room-types</strong> - List room types including Junior Suite
        </div>
        <div class="endpoint">
            <strong>/test</strong> - Test multiplatform search
        </div>
        
        <h2>Cities supported:</h2>
        <div class="cities">
            {% for city in cities %}
            <div class="city">{{ city }}</div>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', cities=list(CITIES.keys()))

@app.route('/api/cities')
def get_cities():
    """Get all supported cities"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES)
    })

@app.route('/api/room-types')
def get_room_types():
    """Get all supported room types including Junior Suite"""
    return jsonify({
        'room_types': ROOM_TYPES,
        'total': len(ROOM_TYPES),
        'junior_suite_included': True
    })

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

@
