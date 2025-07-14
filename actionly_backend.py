# STAYFINDR BACKEND - European Hotel Search Engine
# Flask backend with RapidAPI Booking.com integration + Hotels.com /Hotel/Search
# FIXED: Error handling + Your working Hotels.com endpoint

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
RAPIDAPI_HOST_HOTELS = "hotels-com.p.rapidapi.com"

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

# Room Type Configuration with Junior Suite
ROOM_TYPES = {
    'single': {
        'name': 'Single Room',
        'description': 'Perfect for solo travelers',
        'guests': 1,
        'keywords': ['single', 'solo', 'individual']
    },
    'double': {
        'name': 'Double Room',
        'description': 'Ideal for couples',
        'guests': 2,
        'keywords': ['double', 'couple', 'standard', 'queen', 'king']
    },
    'family': {
        'name': 'Family Room',
        'description': 'Spacious accommodation for families',
        'guests': 4,
        'keywords': ['family', 'triple', 'quad', 'bunk', 'connecting']
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'description': 'Spacious room with sitting area',
        'guests': 2,
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded', 'deluxe']
    },
    'suite': {
        'name': 'Suite/Apartment',
        'description': 'Luxury accommodation with separate living area',
        'guests': 3,
        'keywords': ['suite', 'apartment', 'penthouse', 'presidential', 'luxury', 'executive']
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

def search_hotels_com_api(city, checkin, checkout, adults):
    """Search hotels using Hotels.com /Hotel/Search endpoint (YOUR WORKING ENDPOINT)"""
    url = "https://hotels-com.p.rapidapi.com/Hotel/Search"
    
    querystring = {
        "query": city,
        "checkIn": checkin,
        "checkOut": checkout,
        "adults": adults,
        "rooms": 1,
        "locale": "en_US",
        "currency": "USD"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_HOTELS
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"Hotels.com API response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Hotels.com API response: {json.dumps(data, indent=2)[:500]}...")
            return data
        else:
            print(f"Hotels.com API error: {response.status_code} - {response.text}")
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
    
    # Priority 2: Create hotel name-based search URL (IMPROVED METHOD)
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('propertyId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id and hotel_name:
        # Get country code for the city
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        
        # Encode hotel name properly for URL
        hotel_name_encoded = quote_plus(hotel_name)
        
        # Create hotel name-based search URL similar to your example
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
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('hotelId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id:
        # Use hotel ID for direct booking
        return f"https://www.hotels.com/hotel/details.html?hotel-id={hotel_id}&check-in={checkin}&check-out={checkout}&adults={adults}&rooms={rooms}"
    else:
        # Fallback to search by name
        hotel_name_encoded = quote_plus(hotel_name)
        return f"https://www.hotels.com/search.do?q-destination={hotel_name_encoded}&q-check-in={checkin}&q-check-out={checkout}&q-rooms={rooms}&q-room-0-adults={adults}"

def analyze_room_type(hotel_name, room_type):
    """Analyze if hotel matches requested room type"""
    if room_type not in ROOM_TYPES:
        return False, ""
    
    room_config = ROOM_TYPES[room_type]
    hotel_name_lower = hotel_name.lower()
    
    # Check if hotel name contains room type keywords
    for keyword in room_config['keywords']:
        if keyword in hotel_name_lower:
            return True, f"✨ {room_config['name']} - {room_config['description']}"
    
    return False, ""

def process_hotel_data_booking(hotels_data, city_info, checkin, checkout, adults, rooms, city_key, room_type='double'):
    """Process and format Booking.com hotel data with proper booking URLs"""
    processed_hotels = []
    
    for i, hotel in enumerate(hotels_data):
        try:
            # Extract hotel information with error handling
            hotel_name = hotel.get('name', 'Unknown Hotel')
            
            # Analyze room type match
            is_match, room_description = analyze_room_type(hotel_name, room_type)
            
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
            
            # Extract pricing information with error handling
            price = 'N/A'
            if 'priceBreakdown' in hotel and hotel['priceBreakdown']:
                price_info = hotel['priceBreakdown'].get('grossPrice', {})
                if price_info and 'value' in price_info:
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
            
            # Extract rating with error handling
            rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
            if rating:
                rating = float(rating) / 2 if rating > 5 else float(rating)  # Normalize to 5-point scale
            else:
                rating = 4.0
            
            # Extract address with error handling
            address = hotel.get('address', city_info['name'])
            
            # Create optimized booking URL with hotel name
            booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key)
            
            processed_hotel = {
                'id': hotel.get('id') or hotel.get('hotel_id') or f"booking_{i}",
                'name': hotel_name,
                'address': address,
                'coordinates': coordinates,
                'price': price,
                'rating': rating,
                'booking_url': booking_url,
                'platform': 'Booking.com',
                'currency': 'EUR',
                'room_match': is_match,
                'room_description': room_description if room_description else ROOM_TYPES[room_type]['description']
            }
            
            processed_hotels.append(processed_hotel)
            
        except Exception as e:
            print(f"Error processing Booking.com hotel {i}: {e}")
            continue
    
    return processed_hotels

def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms, room_type='double'):
    """Process Hotels.com hotel data - WORKING VERSION FROM YESTERDAY"""
    processed_hotels = []
    
    # ✅ Safe data structure check (from yesterday's fix)
    if not isinstance(hotels_data, dict) or 'data' not in hotels_data:
        print("Hotels.com: Invalid data structure")
        return processed_hotels
    
    data = hotels_data.get('data')
    properties = []
    
    # 🎯 Extract hotel list (yesterday's working extraction)
    if isinstance(data, dict):
        properties = (
            data.get('propertySearch', {}).get('properties') or
            data.get('properties') or []
        )
    elif isinstance(data, list):
        properties = data
    
    print(f"Found {len(properties)} Hotels.com properties")
    
    for i, hotel in enumerate(properties[:25]):
        if not isinstance(hotel, dict):
            continue
        
        try:
            # 🏨 Hotel name (safe extraction)
            hotel_name = hotel.get('name') or f"Hotel {i+1}"
            
            # Analyze room type match
            is_match, room_description = analyze_room_type(hotel_name, room_type)
            
            # 🗺️ Coordinates with safe fallbacks (yesterday's working method)
            coordinates = city_info.get('coordinates', [0.0, 0.0])
            lat = (
                hotel.get('mapMarker', {}).get('latLong', {}).get('lat') or
                hotel.get('mapMarker', {}).get('latLong', {}).get('latitude') or
                hotel.get('coordinate', {}).get('lat') or
                hotel.get('coordinate', {}).get('latitude')
            )
            lon = (
                hotel.get('mapMarker', {}).get('latLong', {}).get('lon') or
                hotel.get('mapMarker', {}).get('latLong', {}).get('longitude') or
                hotel.get('coordinate', {}).get('lon') or
                hotel.get('coordinate', {}).get('longitude')
            )
            
            try:
                coordinates = [float(lat), float(lon)]
            except (TypeError, ValueError):
                # Keep city coordinates as fallback
                base_lat, base_lng = city_info['coordinates']
                coordinates = [
                    base_lat + (i * 0.01) - 0.05,
                    base_lng + (i * 0.01) - 0.05
                ]
            
            # 💰 Price (yesterday's working extraction)
            price = hotel.get('price', {}).get('lead', {}).get('amount')
            try:
                price = int(price)
            except (TypeError, ValueError):
                price = 'N/A'
            
            # ⭐ Guest rating (safe extraction)
            rating = hotel.get('reviews', {}).get('score') or hotel.get('guestReviews', {}).get('rating')
            try:
                rating = float(rating)
            except (TypeError, ValueError):
                rating = 4.0
            
            # 🔗 Booking URL (working from yesterday)
            property_id = hotel.get('id') or hotel.get('propertyId') or str(i)
            hotels_url = (
                f"https://hotels.com/h{property_id}.Hotel-Information?"
                f"checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
            )
            
            # 🏷️ Address with safe control (yesterday's method)
            address = city_info.get('name')
            neighborhood = hotel.get('neighborhood')
            if isinstance(neighborhood, dict):
                address = neighborhood.get('name') or address
            else:
                street = hotel.get('address', {}).get('streetAddress')
                if street:
                    address = street
            
            # 📦 Collect information
            processed_hotel = {
                'id': f"hotels_{property_id}",
                'name': hotel_name,
                'address': address,
                'coordinates': coordinates,
                'price': price,
                'rating': rating,
                'platform': 'Hotels.com',
                'platform_logo': '🏛️',
                'booking_url': hotels_url,
                'currency': 'USD',
                'room_match': is_match,
                'room_description': room_description if room_description else ROOM_TYPES[room_type]['description']
            }
            
            processed_hotels.append(processed_hotel)
            
        except Exception as e:
            print(f"Hotels.com hotel {i}: Processing error: {e}")
            continue
    
    print(f"Successfully processed {len(processed_hotels)} Hotels.com hotels")
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
            .error-fix { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ffc107; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API</h1>
        <p>Flask backend for European hotel search with multiplatform comparison</p>
        
        <div class="error-fix">
            <strong>🔧 FIXED: Error Handling</strong><br>
            Added comprehensive error handling for Hotels.com API None responses
        </div>
        
        <div class="feature">
            <strong>✅ NEW: Hotels.com /Hotel/Search Integration</strong><br>
            Using your working endpoint for real Hotels.com data
        </div>
        
        <div class="feature">
            <strong>🏨 Room Type Filter with Junior Suite</strong><br>
            Smart filtering for Single, Double, Family, Junior Suite, and Suite/Apartment
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels</strong> - Get hotels from multiple platforms<br>
            Parameters: city, checkin, checkout, adults, rooms, room_type<br>
            <em>Now with Hotels.com /Hotel/Search integration + error handling</em>
        </div>
        <div class="endpoint">
            <strong>/api/room-types</strong> - List all supported room types
        </div>
        <div class="endpoint">
            <strong>/test</strong> - Test multiplatform Stockholm hotels
        </div>
        <div class="endpoint">
            <strong>/test-hotels-com-api</strong> - Test Hotels.com API directly
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

@app.route('/api/room-types')
def get_room_types():
    """Get all supported room types"""
    return jsonify({
        'room_types': ROOM_TYPES,
        'total': len(ROOM_TYPES)
    })

@app.route('/api/cities')
def get_cities():
    """Get all supported cities"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES)
    })

@app.route('/test-hotels-com-api')
def test_hotels_com_api():
    """Test Hotels.com API directly with your /Hotel/Search endpoint"""
    print("Testing Hotels.com API...")
    
    # Test with Stockholm
    city = "Stockholm"
    checkin = "2025-07-15"
    checkout = "2025-07-16"
    adults = 2
    
    hotels_data = search_hotels_com_api(city, checkin, checkout, adults)
    
    if hotels_data:
        return jsonify({
            'status': 'SUCCESS!',
            'endpoint': '/Hotel/Search',
            'city_searched': city,
            'raw_data_structure': list(hotels_data.keys()) if isinstance(hotels_data, dict) else 'List format',
            'hotels_found': len(hotels_data.get('data', [])) if isinstance(hotels_data, dict) and 'data' in hotels_data else 'Unknown structure',
            'sample_data': str(hotels_data)[:500] + '...' if len(str(hotels_data)) > 500 else str(hotels_data),
            'hotels_com': 'real_api_/Hotel/Search'
        })
    else:
        return jsonify({
            'status': 'FAILED',
            'endpoint': '/Hotel/Search',
            'error': 'No data returned from Hotels.com API',
            'hotels_com': 'api_failed'
        })

@app.route('/api/hotels')
def get_hotels_multiplatform():
    """Get hotels from multiple platforms with room type filter"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-15')
    checkout = request.args.get('checkout', '2025-07-16')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    room_type = request.args.get('room_type', 'double')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    if room_type not in ROOM_TYPES:
        return jsonify({'error': f'Room type {room_type} not supported'}), 400
    
    city_info = CITIES[city]
    all_hotels = []
    
    # 1. Get Booking.com hotels
    print(f"Searching Booking.com for {city}...")
    booking_hotels = []
    try:
        location_id = get_location_id_booking(city_info['search_query'])
        if location_id:
            booking_data = search_hotels_booking_api(location_id, checkin, checkout, adults, rooms)
            if booking_data and 'data' in booking_data:
                booking_hotels = process_hotel_data_booking(
                    booking_data['data'][:25],  # Limit to 25 hotels
                    city_info,
                    checkin,
                    checkout,
                    adults,
                    rooms,
                    city,
                    room_type
                )
                print(f"Found {len(booking_hotels)} Booking.com hotels")
    except Exception as e:
        print(f"Booking.com error: {e}")
    
    # 2. Get Hotels.com hotels with FIXED error handling
    print(f"Searching Hotels.com for {city}...")
    hotels_com_hotels = []
    try:
        hotels_data = search_hotels_com_api(city_info['search_query'], checkin, checkout, adults)
        if hotels_data:
            hotels_com_hotels = process_hotels_com_hotels(
                hotels_data,
                city_info,
                checkin,
                checkout,
                adults,
                rooms,
                room_type
            )
            print(f"Found {len(hotels_com_hotels)} Hotels.com hotels")
    except Exception as e:
        print(f"Hotels.com error: {e}")
        # Don't let Hotels.com errors break the entire response
    
    # 3. Combine results
    all_hotels = booking_hotels + hotels_com_hotels
    
    # 4. Sort by room type match first, then by price
    def sort_key(hotel):
        return (not hotel.get('room_match', False), hotel.get('price', 999999) if hotel.get('price') != 'N/A' else 999999)
    
    all_hotels.sort(key=sort_key)
    
    return jsonify({
        'city': city_info['name'],
        'hotels': all_hotels,
        'total_found': len(all_hotels),
        'booking_com_count': len(booking_hotels),
        'hotels_com_count': len(hotels_com_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout,
            'adults': adults,
            'rooms': rooms,
            'room_type': room_type
        },
        'room_filter': 'enabled',
        'room_type': room_type,
        'room_description': ROOM_TYPES[room_type]['description'],
        'booking_optimization': 'enabled',
        'localization': 'enabled',
        'url_type': 'hotel_name_based',
        'hotels_com': 'real_api_/Hotel/Search',
        'error_handling': 'fixed'
    })

@app.route('/test')
def test_multiplatform():
    """Test endpoint with multiplatform Stockholm hotels"""
    return get_hotels_multiplatform()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend...")
    print("🏨 Supporting 29 European cities")
    print("🔧 FIXED: Error handling for Hotels.com API")
    print("🌍 NEW: Hotels.com /Hotel/Search integration")
    print("🏨 Room Types: Single, Double, Family, Junior Suite, Suite/Apartment")
    print("🔗 Frontend will connect to: http://localhost:5000")
    print("📋 Test API: http://localhost:5000/test")
    print("🧪 Test Hotels.com: http://localhost:5000/test-hotels-com-api")
    print("✅ Comprehensive error handling enabled")
    
    # Use PORT environment variable for deployment (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
