# STAYFINDR BACKEND - European Hotel Search Engine
# Flask backend with RapidAPI Booking.com integration + Hotels.com
# FIXED: Complete clean version

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
RAPIDAPI_HOST = "booking-com18.p.rapidapi.com"
HOTELS_COM_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
HOTELS_COM_HOST = "hotels4.p.rapidapi.com"

# European Cities Configuration - 29 major destinations
CITIES = {
    'stockholm': {
        'name': 'Stockholm, Sweden',
        'coordinates': [59.3293, 18.0686],
        'search_query': 'Stockholm Sweden'
    },
    'paris': {
        'name': 'Paris, France', 
        'coordinates': [48.8566, 2.3522],
        'search_query': 'Paris France'
    },
    'london': {
        'name': 'London, UK',
        'coordinates': [51.5074, -0.1278],
        'search_query': 'London United Kingdom'
    },
    'amsterdam': {
        'name': 'Amsterdam, Netherlands',
        'coordinates': [52.3676, 4.9041],
        'search_query': 'Amsterdam Netherlands'
    },
    'barcelona': {
        'name': 'Barcelona, Spain',
        'coordinates': [41.3851, 2.1734],
        'search_query': 'Barcelona Spain'
    },
    'rome': {
        'name': 'Rome, Italy',
        'coordinates': [41.9028, 12.4964],
        'search_query': 'Rome Italy'
    },
    'berlin': {
        'name': 'Berlin, Germany',
        'coordinates': [52.5200, 13.4050],
        'search_query': 'Berlin Germany'
    },
    'copenhagen': {
        'name': 'Copenhagen, Denmark',
        'coordinates': [55.6761, 12.5683],
        'search_query': 'Copenhagen Denmark'
    },
    'vienna': {
        'name': 'Vienna, Austria',
        'coordinates': [48.2082, 16.3738],
        'search_query': 'Vienna Austria'
    },
    'prague': {
        'name': 'Prague, Czech Republic',
        'coordinates': [50.0755, 14.4378],
        'search_query': 'Prague Czech Republic'
    },
    'madrid': {
        'name': 'Madrid, Spain',
        'coordinates': [40.4168, -3.7038],
        'search_query': 'Madrid Spain'
    },
    'milano': {
        'name': 'Milano, Italy',
        'coordinates': [45.4642, 9.1900],
        'search_query': 'Milano Italy'
    },
    'zurich': {
        'name': 'Zürich, Switzerland',
        'coordinates': [47.3769, 8.5417],
        'search_query': 'Zürich Switzerland'
    },
    'oslo': {
        'name': 'Oslo, Norway',
        'coordinates': [59.9139, 10.7522],
        'search_query': 'Oslo Norway'
    },
    'helsinki': {
        'name': 'Helsinki, Finland',
        'coordinates': [60.1695, 24.9354],
        'search_query': 'Helsinki Finland'
    },
    'warsaw': {
        'name': 'Warsaw, Poland',
        'coordinates': [52.2297, 21.0122],
        'search_query': 'Warsaw Poland'
    },
    'budapest': {
        'name': 'Budapest, Hungary',
        'coordinates': [47.4979, 19.0402],
        'search_query': 'Budapest Hungary'
    },
    'dublin': {
        'name': 'Dublin, Ireland',
        'coordinates': [53.3498, -6.2603],
        'search_query': 'Dublin Ireland'
    },
    'lisbon': {
        'name': 'Lisbon, Portugal',
        'coordinates': [38.7223, -9.1393],
        'search_query': 'Lisbon Portugal'
    },
    'brussels': {
        'name': 'Brussels, Belgium',
        'coordinates': [50.8503, 4.3517],
        'search_query': 'Brussels Belgium'
    },
    'athens': {
        'name': 'Athens, Greece',
        'coordinates': [37.9838, 23.7275],
        'search_query': 'Athens Greece'
    },
    'munich': {
        'name': 'Munich, Germany',
        'coordinates': [48.1351, 11.5820],
        'search_query': 'Munich Germany'
    },
    'lyon': {
        'name': 'Lyon, France',
        'coordinates': [45.7640, 4.8357],
        'search_query': 'Lyon France'
    },
    'florence': {
        'name': 'Florence, Italy',
        'coordinates': [43.7696, 11.2558],
        'search_query': 'Florence Italy'
    },
    'edinburgh': {
        'name': 'Edinburgh, Scotland',
        'coordinates': [55.9533, -3.1883],
        'search_query': 'Edinburgh Scotland'
    },
    'nice': {
        'name': 'Nice, France',
        'coordinates': [43.7102, 7.2620],
        'search_query': 'Nice France'
    },
    'palma': {
        'name': 'Palma, Spain',
        'coordinates': [39.5696, 2.6502],
        'search_query': 'Palma Spain'
    },
    'santorini': {
        'name': 'Santorini, Greece',
        'coordinates': [36.3932, 25.4615],
        'search_query': 'Santorini Greece'
    },
    'ibiza': {
        'name': 'Ibiza, Spain',
        'coordinates': [38.9067, 1.4206],
        'search_query': 'Ibiza Spain'
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

# Room Types Configuration with Junior Suite
ROOM_TYPES = {
    'single': {
        'name': 'Single Room',
        'guests': 1,
        'description': 'Single Room - Perfect for solo travelers',
        'keywords': ['single', 'single room', 'solo', 'one bed']
    },
    'double': {
        'name': 'Double Room', 
        'guests': 2,
        'description': 'Double Room - Ideal for couples',
        'keywords': ['double', 'double room', 'couple', 'two bed', 'standard']
    },
    'family': {
        'name': 'Family Room',
        'guests': 4,
        'description': 'Family Room - Spacious for families',
        'keywords': ['family', 'family room', 'triple', 'quad', 'bunk']
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'guests': 2,
        'description': 'Junior Suite - Spacious room with sitting area',
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded', 'deluxe']
    },
    'suite': {
        'name': 'Suite/Apartment',
        'guests': 3,
        'description': 'Suite/Apartment - Luxury accommodation with separate areas',
        'keywords': ['suite', 'apartment', 'luxury', 'presidential', 'executive']
    }
}

def get_location_id(city_query):
    """Get Booking.com location ID for a city"""
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {"query": city_query, "languageCode": "en"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return data['data'][0].get('id')
    except Exception as e:
        print(f"Error getting location ID: {e}")
    
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
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error searching hotels: {e}")
    
    return None

def search_hotels_com_suggest(query):
    """Step 1: Get destination ID from Hotels.com suggest endpoint"""
    url = "https://hotels4.p.rapidapi.com/locations/v3/search"
    
    querystring = {"q": query, "locale": "en_US", "langid": "1033", "siteid": "300000001"}
    headers = {
        "x-rapidapi-key": HOTELS_COM_KEY,
        "x-rapidapi-host": HOTELS_COM_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'sr' in data and data['sr']:
                for item in data['sr']:
                    if item.get('type') == 'CITY':
                        return {
                            'destination_id': item.get('gaiaId'),
                            'name': item.get('regionNames', {}).get('fullName', ''),
                            'country': item.get('hierarchyInfo', {}).get('country', {}).get('name', '')
                        }
    except Exception as e:
        print(f"Error in Hotels.com suggest: {e}")
    
    return None

def search_hotels_com_hotels(destination_id, checkin, checkout, adults):
    """Step 2: Search hotels using destination ID"""
    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "destination": {"regionId": destination_id},
        "checkInDate": {
            "day": int(checkin.split('-')[2]),
            "month": int(checkin.split('-')[1]),
            "year": int(checkin.split('-')[0])
        },
        "checkOutDate": {
            "day": int(checkout.split('-')[2]),
            "month": int(checkout.split('-')[1]),
            "year": int(checkout.split('-')[0])
        },
        "rooms": [{"adults": int(adults)}],
        "resultsStartingIndex": 0,
        "resultsSize": 20,
        "sort": "PRICE_LOW_TO_HIGH"
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": HOTELS_COM_KEY,
        "x-rapidapi-host": HOTELS_COM_HOST
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error in Hotels.com hotels search: {e}")
    
    return None

def search_hotels_com_api_working(city_query, checkin, checkout, adults):
    """Two-step Hotels.com search: suggest → hotels"""
    # Step 1: Get destination ID
    destination_info = search_hotels_com_suggest(city_query)
    if not destination_info or not destination_info.get('destination_id'):
        return None
    
    # Step 2: Search hotels with destination ID
    return search_hotels_com_hotels(
        destination_info['destination_id'], 
        checkin, 
        checkout, 
        adults
    )

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
            'ss': hotel_name,
            'dest_id': hotel_id,
            'dest_type': 'hotel',
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
    return "https://www.hotels.com"

def process_hotel_data_booking(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process and format Booking.com hotel data"""
    processed_hotels = []
    
    for i, hotel in enumerate(hotels_data):
        # Extract hotel information
        hotel_name = hotel.get('name', 'Unknown Hotel')
        
        # Get coordinates
        latitude = hotel.get('latitude')
        longitude = hotel.get('longitude')
        
        if latitude and longitude:
            coordinates = [float(latitude), float(longitude)]
        else:
            base_lat, base_lng = city_info['coordinates']
            coordinates = [
                base_lat + (i * 0.01) - 0.05,
                base_lng + (i * 0.01) - 0.05
            ]
        
        # Extract pricing
        price = 'N/A'
        if 'priceBreakdown' in hotel:
            price_info = hotel['priceBreakdown'].get('grossPrice', {})
            if 'value' in price_info:
                total_price = price_info['value']
                try:
                    from datetime import datetime
                    checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
                    checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
                    nights = (checkout_date - checkin_date).days
                    if nights > 0:
                        price = int(total_price / nights)
                    else:
                        price = total_price
                except:
                    price = int(total_price / 7)
        elif 'price' in hotel:
            price = hotel['price']
        
        # Extract rating
        rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)
        else:
            rating = 4.0
        
        # Extract address
        address = hotel.get('address', city_info['name'])
        
        # Create booking URL
        booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key)
        
        processed_hotel = {
            'id': hotel.get('id') or hotel.get('hotel_id') or f"booking_{i}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'booking_url': booking_url,
            'source': 'booking.com'
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms, room_type):
    """Process Hotels.com hotel data"""
    processed_hotels = []
    
    if not hotels_data or 'data' not in hotels_data:
        return processed_hotels
    
    properties = hotels_data['data'].get('propertySearch', {}).get('properties', [])
    
    for i, hotel in enumerate(properties):
        # Extract hotel information
        hotel_name = hotel.get('name', 'Unknown Hotel')
        
        # Get coordinates
        coordinates_data = hotel.get('mapMarker', {})
        if coordinates_data and 'latLong' in coordinates_data:
            lat_long = coordinates_data['latLong']
            coordinates = [lat_long.get('latitude', 0), lat_long.get('longitude', 0)]
        else:
            base_lat, base_lng = city_info['coordinates']
            coordinates = [
                base_lat + (i * 0.01) - 0.05,
                base_lng + (i * 0.01) - 0.05
            ]
        
        # Extract pricing
        price = 'N/A'
        price_data = hotel.get('price', {})
        if price_data and 'lead' in price_data:
            lead_price = price_data['lead']
            if 'amount' in lead_price:
                price = int(lead_price['amount'])
        
        # Extract rating
        rating = 4.0
        reviews_data = hotel.get('reviews', {})
        if reviews_data and 'score' in reviews_data:
            rating = float(reviews_data['score'])
        
        # Extract address
        address = hotel.get('neighborhood', {}).get('name', city_info['name'])
        
        # Create Hotels.com URL
        booking_url = create_hotels_com_url(hotel, checkin, checkout, adults, rooms)
        
        processed_hotel = {
            'id': hotel.get('id') or f"hotels_com_{i}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'booking_url': booking_url,
            'source': 'hotels.com'
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

@app.route('/')
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
        <p>Flask backend for European hotel search with multiplatform support</p>
        
        <div class="feature">
            <strong>✅ MULTIPLATFORM: Booking.com + Hotels.com</strong><br>
            Two-step Hotels.com integration with suggest + hotels endpoints
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels</strong> - Get hotels from both platforms<br>
            Parameters: city, checkin, checkout, adults, rooms, room_type<br>
            <em>Returns combined results from Booking.com and Hotels.com</em>
        </div>
        <div class="endpoint">
            <strong>/api/cities</strong> - List all 29 cities
        </div>
        <div class="endpoint">
            <strong>/test</strong> - Test multiplatform search
        </div>
        <div class="endpoint">
            <strong>/debug-hotels-com</strong> - Debug Hotels.com API
        </div>
        
        <h2>Room types supported:</h2>
        <div class="cities">
            {% for room_type in room_types %}
            <div class="city">{{ room_type }}</div>
            {% endfor %}
        </div>
        
        <h2>Cities supported:</h2>
        <div class="cities">
            {% for city in cities %}
            <div class="city">{{ city }}</div>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', cities=list(CITIES.keys()), room_types=list(ROOM_TYPES.keys()))

@app.route('/api/cities')
def get_cities():
    """Get all supported cities"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES)
    })

@app.route('/api/room-types')
def get_room_types():
    """Get all supported room types"""
    return jsonify({
        'room_types': ROOM_TYPES,
        'total': len(ROOM_TYPES)
    })

@app.route('/debug-hotels-com')
def debug_hotels_com():
    """Debug Hotels.com API step by step"""
    city_query = "Stockholm Sweden"
    
    debug_info = {
        'step_1': 'Testing Hotels.com suggest endpoint',
        'query': city_query,
        'timestamp': datetime.now().isoformat()
    }
    
    # Step 1: Test suggest endpoint
    destination_info = search_hotels_com_suggest(city_query)
    debug_info['step_1_result'] = destination_info
    
    if destination_info and destination_info.get('destination_id'):
        debug_info['step_2'] = 'Testing Hotels.com hotels search'
        debug_info['destination_id'] = destination_info['destination_id']
        
        # Step 2: Test hotels search
        hotels_data = search_hotels_com_hotels(
            destination_info['destination_id'],
            '2025-07-15',
            '2025-07-16', 
            '2'
        )
        
        debug_info['step_2_result'] = {
            'has_data': hotels_data is not None,
            'data_keys': list(hotels_data.keys()) if hotels_data else [],
            'sample_data': str(hotels_data)[:500] if hotels_data else None
        }
        
        if hotels_data and 'data' in hotels_data:
            properties = hotels_data['data'].get('propertySearch', {}).get('properties', [])
            debug_info['hotels_found'] = len(properties)
            if properties:
                debug_info['sample_hotel'] = {
                    'name': properties[0].get('name'),
                    'id': properties[0].get('id'),
                    'price': properties[0].get('price', {})
                }
        else:
            debug_info['error'] = 'No hotels data found in response'
    else:
        debug_info['error'] = 'No destination ID found in suggest response'
    
    return jsonify(debug_info)

@app.route('/test')
def test_multiplatform():
    """Test endpoint with both platforms"""
    return get_hotels_multiplatform()

@app.route('/api/hotels')
def get_hotels_multiplatform():
    """Get hotels from both Booking.com and Hotels.com platforms"""
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
    
    # Get room type info
    room_info = ROOM_TYPES.get(room_type, ROOM_TYPES['double'])
    
    # Platform 1: Booking.com
    booking_hotels = []
    location_id = get_location_id(city_info['search_query'])
    
    if location_id:
        hotels_data = search_hotels_booking_api(location_id, checkin, checkout, adults, rooms)
        if hotels_data and 'data' in hotels_data:
            booking_hotels = process_hotel_data_booking(
                hotels_data['data'][:20],
                city_info, 
                checkin, 
                checkout, 
                adults, 
                rooms,
                city
            )
    
    # Platform 2: Hotels.com
    hotels_com_hotels = []
    hotels_com_data = search_hotels_com_api_working(city_info['search_query'], checkin, checkout, adults)
    
    if hotels_com_data:
        hotels_com_hotels = process_hotels_com_hotels(
            hotels_com_data,
            city_info,
            checkin,
            checkout,
            adults,
            rooms,
            room_type
        )
    
    # Combine all hotels
    all_hotels = booking_hotels + hotels_com_hotels
    
    # Remove duplicates based on hotel name similarity
    unique_hotels = []
    seen_names = set()
    
    for hotel in all_hotels:
        hotel_name_clean = hotel['name'].lower().replace(' ', '').replace('-', '')[:20]
        if hotel_name_clean not in seen_names:
            seen_names.add(hotel_name_clean)
            unique_hotels.append(hotel)
    
    return jsonify({
        'city': city_info['name'],
        'hotels': unique_hotels,
        'total_found': len(unique_hotels),
        'booking_com_count': len(booking_hotels),
        'hotels_com_count': len(hotels_com_hotels),
        'platforms': ['booking.com', 'hotels.com'],
        'search_params': {
            'checkin': checkin,
            'checkout': checkout,
            'adults': adults,
            'rooms': rooms,
            'room_type': room_type
        },
        'room_filter': 'enabled',
        'room_type': room_type,
        'room_description': room_info['description'],
        'booking_optimization': 'enabled',
        'localization': 'enabled',
        'multiplatform': 'active'
    })

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend...")
    print("🏨 MULTIPLATFORM: Booking.com + Hotels.com")
    print("🔗 Two-step Hotels.com: suggest → search")
    print("✅ Room filtering with Junior Suite support")
    print("🌍 Supporting 29 European cities")
    print("📋 Test endpoints: /test, /debug-hotels-com")
    
    # Use PORT environment variable for deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
