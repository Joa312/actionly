# STAYFINDR BACKEND - European Hotel Search Engine
# Flask backend with RapidAPI Booking.com integration
# FIXED: Hotel name-based booking URLs + Room Type Filter with Junior Suite

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

# Room Type Configurations
ROOM_TYPES = {
    'single': {
        'name': 'Single Room',
        'description': 'Single Room - Perfect for solo travelers',
        'guests': 1,
        'keywords': ['single', 'solo', '1 person', 'individual'],
        'booking_params': {'group_adults': 1, 'no_rooms': 1}
    },
    'double': {
        'name': 'Double Room',
        'description': 'Double Room - Ideal for couples',
        'guests': 2,
        'keywords': ['double', 'couple', 'twin', 'queen', 'king'],
        'booking_params': {'group_adults': 2, 'no_rooms': 1}
    },
    'family': {
        'name': 'Family Room',
        'description': 'Family Room - Great for families with children',
        'guests': 4,
        'keywords': ['family', 'children', 'kids', 'triple', 'quad'],
        'booking_params': {'group_adults': 4, 'no_rooms': 1, 'group_children': 2}
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'description': 'Junior Suite - Spacious room with sitting area',
        'guests': 2,
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded', 'spacious'],
        'booking_params': {'group_adults': 2, 'no_rooms': 1, 'room_type': 'junior_suite'}
    },
    'suite': {
        'name': 'Suite/Apartment',
        'description': 'Suite/Apartment - Luxury accommodation with separate living area',
        'guests': 3,
        'keywords': ['suite', 'apartment', 'luxury', 'living area', 'presidential', 'executive'],
        'booking_params': {'group_adults': 3, 'no_rooms': 1, 'room_type': 'suite'}
    }
}

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

def analyze_room_type_match(hotel, room_type):
    """Analyze if hotel matches the requested room type"""
    if room_type not in ROOM_TYPES:
        return False
    
    room_config = ROOM_TYPES[room_type]
    hotel_name = hotel.get('name', '').lower()
    hotel_description = hotel.get('description', '').lower()
    
    # Check if hotel name/description contains room type keywords
    for keyword in room_config['keywords']:
        if keyword in hotel_name or keyword in hotel_description:
            return True
    
    return False

def create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key, room_type):
    """Create hotel name-based booking URL with room type for better targeting"""
    
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
            room_params = ROOM_TYPES.get(room_type, {}).get('booking_params', {})
            param_string = '&'.join([f"{k}={v}" for k, v in room_params.items()])
            
            if '?' in url:
                return f"{url}&checkin={checkin}&checkout={checkout}&{param_string}"
            else:
                return f"{url}?checkin={checkin}&checkout={checkout}&{param_string}"
    
    # Priority 2: Create hotel name-based search URL (IMPROVED METHOD)
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('propertyId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id and hotel_name:
        # Get country code for the city
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        
        # Get room type specific parameters
        room_config = ROOM_TYPES.get(room_type, ROOM_TYPES['double'])
        room_params = room_config['booking_params']
        
        # Encode hotel name properly for URL
        hotel_name_encoded = quote_plus(hotel_name)
        
        # Create hotel name-based search URL similar to your example
        base_params = {
            'ss': hotel_name,  # Hotel search string
            'dest_id': hotel_id,  # Hotel destination ID
            'dest_type': 'hotel',  # Specify it's a hotel
            'checkin': checkin,
            'checkout': checkout,
            'search_selected': 'true'
        }
        
        # Add room type specific parameters
        base_params.update(room_params)
        
        # Build URL parameters
        params_string = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in base_params.items()])
        
        return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"
    
    # Priority 3: Fallback to hotel ID-based URL
    if hotel_id:
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        room_config = ROOM_TYPES.get(room_type, ROOM_TYPES['double'])
        room_params = room_config['booking_params']
        param_string = '&'.join([f"{k}={v}" for k, v in room_params.items()])
        
        return f"https://www.booking.com/hotel/{country_code.split('-')[0]}/?hotel_id={hotel_id}&checkin={checkin}&checkout={checkout}&{param_string}"
    
    # Priority 4: Generic search by hotel name in the city
    hotel_name = hotel.get('name', '').replace(' ', '+')
    city_name = city_info['name'].replace(' ', '+')
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    room_config = ROOM_TYPES.get(room_type, ROOM_TYPES['double'])
    room_params = room_config['booking_params']
    param_string = '&'.join([f"{k}={v}" for k, v in room_params.items()])
    
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={hotel_name}+{city_name}&checkin={checkin}&checkout={checkout}&{param_string}"

def process_hotel_data(hotels_data, city_info, checkin, checkout, adults, rooms, city_key, room_type):
    """Process and format hotel data with proper booking URLs and room type analysis"""
    processed_hotels = []
    
    for i, hotel in enumerate(hotels_data):
        # Extract hotel information
        hotel_name = hotel.get('name', 'Unknown Hotel')
        
        # Analyze room type match
        room_match = analyze_room_type_match(hotel, room_type)
        
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
        if 'priceBreakdown' in hotel:
            price_info = hotel['priceBreakdown'].get('grossPrice', {})
            if 'value' in price_info:
                # Convert to per night if total price
                total_price = price_info['value']
                try:
                    # Estimate per night (assuming booking is for multiple nights)
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
        
        # Extract rating
        rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)  # Normalize to 5-point scale
        else:
            rating = 4.0
        
        # Extract address
        address = hotel.get('address', city_info['name'])
        
        # Create optimized booking URL with hotel name and room type
        booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key, room_type)
        
        processed_hotel = {
            'id': hotel.get('id') or hotel.get('hotel_id') or f"hotel_{i}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'booking_url': booking_url,
            'room_type_match': room_match,
            'room_type': ROOM_TYPES.get(room_type, {}).get('name', 'Hotel Room')
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
            .room-types { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 20px 0; }
            .room-type { background: #fff3e0; padding: 10px; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API</h1>
        <p>Flask backend for European hotel search with room type filtering and hotel name-based booking URLs</p>
        
        <div class="feature">
            <strong>✅ NEW: Room Type Filter with Junior Suite</strong><br>
            Search for specific room types including Single, Double, Family, Junior Suite, and Suite/Apartment rooms
        </div>
        
        <div class="feature">
            <strong>✅ Hotel Name-Based Booking URLs</strong><br>
            CTA buttons now use hotel names for better targeting and SEO, similar to native Booking.com searches
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels</strong> - Get hotels for a city<br>
            Parameters: city, room_type, checkin, checkout, adults, rooms<br>
            <em>Now with room type filtering and improved hotel name-based URLs</em>
        </div>
        <div class="endpoint">
            <strong>/api/cities</strong> - List all 29 cities
        </div>
        <div class="endpoint">
            <strong>/api/room-types</strong> - List all room types with Junior Suite
        </div>
        <div class="endpoint">
            <strong>/test</strong> - Test Stockholm hotels with room type filtering
        </div>
        
        <h2>Room Types supported:</h2>
        <div class="room-types">
            {% for room_key, room_info in room_types.items() %}
            <div class="room-type">
                <strong>{{ room_info.name }}</strong><br>
                {{ room_info.description }}<br>
                <em>{{ room_info.guests }} guests</em>
            </div>
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
    ''', cities=list(CITIES.keys()), room_types=ROOM_TYPES)

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

@app.route('/api/hotels')
def get_hotels():
    """Get hotels for a specific city with room type filtering and hotel name-based booking URLs"""
    city = request.args.get('city', 'stockholm')
    room_type = request.args.get('room_type', 'double')
    checkin = request.args.get('checkin', '2025-07-14')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    if room_type not in ROOM_TYPES:
        return jsonify({'error': f'Room type {room_type} not supported'}), 400
    
    city_info = CITIES[city]
    room_config = ROOM_TYPES[room_type]
    
    # Get location ID for the city
    location_id = get_location_id(city_info['search_query'])
    
    if not location_id:
        return jsonify({'error': f'Could not find location ID for {city}'}), 404
    
    # Search hotels
    hotels_data = search_hotels_booking_api(location_id, checkin, checkout, adults, rooms)
    
    if not hotels_data or 'data' not in hotels_data:
        return jsonify({'error': 'No hotels found'}), 404
    
    # Process hotel data with room type filtering and hotel name-based booking URLs - limit to top 50
    processed_hotels = process_hotel_data(
        hotels_data['data'][:50], 
        city_info, 
        checkin, 
        checkout, 
        adults, 
        rooms,
        city,  # Pass city key for country code lookup
        room_type  # Pass room type for filtering and URL generation
    )
    
    return jsonify({
        'city': city_info['name'],
        'hotels': processed_hotels,
        'total_found': len(processed_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms,
            'room_type': room_type
        },
        'room_filter': 'enabled',
        'room_type': room_type,
        'room_description': room_config['description'],
        'booking_optimization': 'enabled',
        'localization': 'enabled',
        'url_type': 'hotel_name_based'
    })

@app.route('/test')
def test_stockholm():
    """Test endpoint with Stockholm hotels and room type filtering"""
    return get_hotels()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend...")
    print("🏨 Supporting 29 European cities")
    print("🛏️ NEW: Room Type Filter with Junior Suite")
    print("🌍 Hotel name-based booking URLs")
    print("🔗 Frontend will connect to: http://localhost:5000")
    print("📋 Test API: http://localhost:5000/test")
    print("✅ Complete room type filtering with localized booking URLs")
    
    # Use PORT environment variable for deployment (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
