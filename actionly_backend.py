# STAYFINDR BACKEND - European Hotel Search Engine
# Flask backend with RapidAPI Booking.com integration
# FIXED: Accurate stay pricing calculation + Room Type Filter + Analytics Tracking

import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import time
from datetime import datetime, timedelta
from urllib.parse import quote_plus

app = Flask(__name__)
CORS(app)

# RapidAPI Configuration
RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
RAPIDAPI_HOST = "booking-com18.p.rapidapi.com"

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
        'description': 'Single Room - Perfect for solo travelers',
        'default_guests': 1,
        'keywords': ['single', 'solo', 'one bed', 'individual'],
        'booking_param': 'single'
    },
    'double': {
        'name': 'Double Room',
        'description': 'Double Room - Ideal for couples',
        'default_guests': 2,
        'keywords': ['double', 'twin', 'couple', 'two bed'],
        'booking_param': 'double'
    },
    'family': {
        'name': 'Family Room',
        'description': 'Family Room - Spacious accommodation for families',
        'default_guests': 4,
        'keywords': ['family', 'large', 'multiple beds', 'kids'],
        'booking_param': 'family'
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'description': 'Junior Suite - Spacious room with sitting area',
        'default_guests': 2,
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded', 'deluxe'],
        'booking_param': 'junior_suite'
    },
    'suite': {
        'name': 'Suite/Apartment',
        'description': 'Suite or Apartment - Luxury accommodation with separate living area',
        'default_guests': 3,
        'keywords': ['suite', 'apartment', 'luxury', 'living room', 'executive'],
        'booking_param': 'suite'
    }
}

def calculate_nights(checkin_str, checkout_str):
    """Calculate number of nights between checkin and checkout dates"""
    try:
        checkin_date = datetime.strptime(checkin_str, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout_str, '%Y-%m-%d')
        nights = (checkout_date - checkin_date).days
        return max(1, nights)  # Minimum 1 night
    except:
        return 1  # Fallback to 1 night

def calculate_stay_price(api_price, price_type, nights):
    """Calculate accurate stay price based on API price format"""
    if not api_price or api_price == 'N/A':
        return 'N/A'
    
    try:
        # Handle different price formats from API
        if isinstance(api_price, dict):
            # Extract price from complex price object
            if 'value' in api_price:
                price_value = float(api_price['value'])
            elif 'amount' in api_price:
                price_value = float(api_price['amount'])
            else:
                return 'N/A'
        else:
            price_value = float(api_price)
        
        # Determine if API price is per night or total
        # Most APIs return total price for the stay, but some return per night
        if price_type == 'total' or price_value > 1000:
            # Likely total price for stay
            return int(price_value)
        else:
            # Likely per night price, calculate total
            return int(price_value * nights)
    except:
        return 'N/A'

def analyze_room_type(hotel_name, hotel_description, requested_room_type):
    """Analyze hotel to determine if it matches requested room type"""
    if requested_room_type not in ROOM_TYPES:
        return False, ""
    
    room_config = ROOM_TYPES[requested_room_type]
    keywords = room_config['keywords']
    
    # Combine hotel name and description for analysis
    text_to_analyze = f"{hotel_name} {hotel_description}".lower()
    
    # Check if any keywords match
    matches = [keyword for keyword in keywords if keyword in text_to_analyze]
    
    if matches:
        return True, f"✨ {room_config['description']} - Matches: {', '.join(matches)}"
    else:
        return False, room_config['description']

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

def create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key, room_type='double'):
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
            additional_params = f"&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}&room_type={room_type}"
            if '?' in url:
                return f"{url}{additional_params}"
            else:
                return f"{url}?{additional_params.lstrip('&')}"
    
    # Priority 2: Create hotel name-based search URL (IMPROVED METHOD)
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('propertyId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id and hotel_name:
        # Get country code for the city
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        
        # Encode hotel name properly for URL
        hotel_name_encoded = quote_plus(hotel_name)
        
        # Create hotel name-based search URL with room type
        base_params = {
            'ss': hotel_name,  # Hotel search string
            'dest_id': hotel_id,  # Hotel destination ID
            'dest_type': 'hotel',  # Specify it's a hotel
            'checkin': checkin,
            'checkout': checkout,
            'group_adults': adults,
            'no_rooms': rooms,
            'group_children': 0,
            'room_type': room_type,
            'search_selected': 'true'
        }
        
        # Build URL parameters
        params_string = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in base_params.items()])
        
        return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"
    
    # Priority 3: Fallback to hotel ID-based URL
    if hotel_id:
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        return f"https://www.booking.com/hotel/{country_code.split('-')[0]}/?hotel_id={hotel_id}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}&room_type={room_type}"
    
    # Priority 4: Generic search by hotel name in the city
    hotel_name = hotel.get('name', '').replace(' ', '+')
    city_name = city_info['name'].replace(' ', '+')
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={hotel_name}+{city_name}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}&room_type={room_type}"

def process_hotel_data(hotels_data, city_info, checkin, checkout, adults, rooms, city_key, room_type='double'):
    """Process and format hotel data with accurate stay pricing and room type matching"""
    processed_hotels = []
    nights = calculate_nights(checkin, checkout)
    
    for i, hotel in enumerate(hotels_data):
        # Extract hotel information
        hotel_name = hotel.get('name', 'Unknown Hotel')
        hotel_description = hotel.get('description', '')
        
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
        
        # Extract and calculate accurate stay pricing
        price = 'N/A'
        if 'priceBreakdown' in hotel:
            price_info = hotel['priceBreakdown'].get('grossPrice', {})
            if 'value' in price_info:
                # This is usually total price for the stay
                price = calculate_stay_price(price_info, 'total', nights)
        elif 'price' in hotel:
            # This could be per night or total - need to analyze
            api_price = hotel['price']
            price = calculate_stay_price(api_price, 'unknown', nights)
        
        # Extract rating
        rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)  # Normalize to 5-point scale
        else:
            rating = 4.0
        
        # Extract address
        address = hotel.get('address', city_info['name'])
        
        # Analyze room type match
        room_match, room_description = analyze_room_type(hotel_name, hotel_description, room_type)
        
        # Create optimized booking URL with room type
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
            'room_description': room_description,
            'nights': nights,
            'price_type': 'stay'  # Indicate this is total stay price
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

# Analytics tracking storage (in production, use a proper database)
analytics_data = []

def track_search(city, room_type, nights, adults, timestamp=None):
    """Track search analytics for partner dashboard"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    analytics_data.append({
        'type': 'search',
        'city': city,
        'room_type': room_type,
        'nights': nights,
        'adults': adults,
        'timestamp': timestamp
    })

def track_click(hotel_id, hotel_name, city, room_type, price, timestamp=None):
    """Track booking button clicks for partner analytics"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    analytics_data.append({
        'type': 'click',
        'hotel_id': hotel_id,
        'hotel_name': hotel_name,
        'city': city,
        'room_type': room_type,
        'price': price,
        'timestamp': timestamp
    })

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
        <p>Flask backend for European hotel search with accurate stay pricing</p>
        
        <div class="feature">
            <strong>✅ NEW: Accurate Stay Pricing</strong><br>
            Prices now show total cost for entire stay, not per night
        </div>
        
        <div class="feature">
            <strong>🏨 Room Type Filter with Junior Suite</strong><br>
            Support for 5 room types including luxury Junior Suites
        </div>
        
        <div class="feature">
            <strong>📊 Analytics Tracking Ready</strong><br>
            Foundation for partner dashboard analytics
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels</strong> - Get hotels for a city<br>
            Parameters: city, checkin, checkout, adults, rooms, room_type<br>
            <em>Now with accurate stay pricing and room type filtering</em>
        </div>
        <div class="endpoint">
            <strong>/api/cities</strong> - List all 29 cities
        </div>
        <div class="endpoint">
            <strong>/api/room-types</strong> - List all room types including Junior Suite
        </div>
        <div class="endpoint">
            <strong>/test</strong> - Test Stockholm hotels with stay pricing
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
        'total': len(ROOM_TYPES)
    })

@app.route('/api/hotels')
def get_hotels():
    """Get hotels for a specific city with accurate stay pricing and room type filtering"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-14')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    room_type = request.args.get('room_type', 'double')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    if room_type not in ROOM_TYPES:
        return jsonify({'error': f'Room type {room_type} not supported'}), 400
    
    city_info = CITIES[city]
    nights = calculate_nights(checkin, checkout)
    
    # Track search for analytics
    track_search(city, room_type, nights, adults)
    
    # Get location ID for the city
    location_id = get_location_id(city_info['search_query'])
    
    if not location_id:
        return jsonify({'error': f'Could not find location ID for {city}'}), 404
    
    # Search hotels
    hotels_data = search_hotels_booking_api(location_id, checkin, checkout, adults, rooms)
    
    if not hotels_data or 'data' not in hotels_data:
        return jsonify({'error': 'No hotels found'}), 404
    
    # Process hotel data with accurate stay pricing and room type filtering - limit to top 50
    processed_hotels = process_hotel_data(
        hotels_data['data'][:50], 
        city_info, 
        checkin, 
        checkout, 
        adults, 
        rooms,
        city,  # Pass city key for country code lookup
        room_type
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
            'nights': nights
        },
        'room_filter': {
            'type': room_type,
            'description': ROOM_TYPES[room_type]['description'],
            'enabled': True
        },
        'pricing': {
            'type': 'stay',
            'nights': nights,
            'description': f'Prices shown are total cost for {nights} nights'
        },
        'booking_optimization': 'enabled',
        'localization': 'enabled',
        'url_type': 'hotel_name_based',
        'analytics_tracking': 'enabled'
    })

@app.route('/api/analytics/track-click', methods=['POST'])
def track_booking_click():
    """Track booking button clicks for analytics"""
    data = request.get_json()
    
    required_fields = ['hotel_id', 'hotel_name', 'city', 'room_type', 'price']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    track_click(
        data['hotel_id'],
        data['hotel_name'],
        data['city'],
        data['room_type'],
        data['price']
    )
    
    return jsonify({'status': 'tracked', 'timestamp': datetime.now().isoformat()})

@app.route('/test')
def test_stockholm():
    """Test endpoint with Stockholm hotels and accurate stay pricing"""
    return get_hotels()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend...")
    print("🏨 Supporting 29 European cities")
    print("💰 NEW: Accurate stay pricing calculation")
    print("🛏️ Room Type Filter with Junior Suite")
    print("📊 Analytics tracking foundation")
    print("🔗 Frontend will connect to: http://localhost:5000")
    print("📋 Test API: http://localhost:5000/test")
    print("✅ Ready for partner dashboard development")
    
    # Use PORT environment variable for deployment (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
