# STAYFINDR BACKEND v10.0 - Complete Dual API Integration
# ENHANCED: Fixed TripAdvisor API, added dual endpoint, mock data fallback
# ADDITIONS: /api/hotels/dual endpoint, better error handling, smart URL generation

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode
import re
import csv

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
from requests.exceptions import RequestException

# --- Initial Configuration ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
if not RAPIDAPI_KEY:
    raise ValueError("FATAL: RAPIDAPI_KEY environment variable is not set.")

CORS(app, origins=["https://joa312.github.io", "http://127.0.0.1:5500", "http://localhost:3000", "http://127.0.0.1:5000"])

# --- API & Data Constants ---
BOOKING_API_HOST = "booking-com18.p.rapidapi.com"
TRIPADVISOR_API_HOST = "tripadvisor1.p.rapidapi.com"  # FIXED: Correct API host
BOOKING_HOTEL_LIMIT = 20
TRIPADVISOR_HOTEL_LIMIT = 15
URL_REGEX = re.compile(r'\d+')

# --- Mock Data for API Fallback ---
MOCK_HOTELS = {
    'stockholm': [
        {'name': 'Hotel Frantz Stockholm', 'price': 152, 'rating': 4.2, 'reviews': 1250},
        {'name': 'Scandic Continental', 'price': 189, 'rating': 4.4, 'reviews': 2100},
        {'name': 'Grand Hotel Stockholm', 'price': 445, 'rating': 4.8, 'reviews': 3200}
    ],
    'paris': [
        {'name': 'Hotel Malte Opera', 'price': 125, 'rating': 4.1, 'reviews': 892},
        {'name': 'Le Meurice', 'price': 850, 'rating': 4.9, 'reviews': 2456},
        {'name': 'Hotel des Grands Boulevards', 'price': 198, 'rating': 4.3, 'reviews': 1234}
    ],
    'london': [
        {'name': 'The Savoy', 'price': 675, 'rating': 4.8, 'reviews': 3456},
        {'name': 'Premier Inn London City', 'price': 89, 'rating': 4.2, 'reviews': 2134},
        {'name': 'The Hoxton, Holborn', 'price': 245, 'rating': 4.5, 'reviews': 1876}
    ]
}

# --- Data Loading ---
def load_cities_from_csv(filename='cities.csv'):
    """Loads cities from CSV, with fallback if file missing."""
    cities = {}
    try:
        with open(filename, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            for i, row in enumerate(reader):
                key = row.get('key')
                if not key:
                    logging.warning(f"Skipping row {i+2} in {filename} due to missing key.")
                    continue
                cities[key] = {
                    'name': row.get('name', 'N/A').replace('"', '').strip(),
                    'search_query': row.get('search_query', ''),
                    'country': row.get('country', 'com'),
                    'tripadvisor_id': row.get('tripadvisor_id', ''),
                    'coordinates': [float(row.get('lat', 0)), float(row.get('lng', 0))]
                }
        logging.info(f"Successfully loaded {len(cities)} cities from {filename}.")
        return cities
    except FileNotFoundError:
        logging.warning(f"CSV file {filename} not found. Using fallback cities.")
        return get_fallback_cities()
    except Exception as e:
        logging.error(f"Failed to read {filename}: {e}. Using fallback cities.")
        return get_fallback_cities()

def get_fallback_cities():
    """Fallback cities if CSV loading fails."""
    return {
        'stockholm': {
            'name': 'Stockholm, Sweden',
            'search_query': 'Stockholm Sweden',
            'country': 'se',
            'tripadvisor_id': '189839',
            'coordinates': [59.3293, 18.0686]
        },
        'paris': {
            'name': 'Paris, France',
            'search_query': 'Paris France',
            'country': 'fr',
            'tripadvisor_id': '187147',
            'coordinates': [48.8566, 2.3522]
        },
        'london': {
            'name': 'London, UK',
            'search_query': 'London United Kingdom',
            'country': 'gb',
            'tripadvisor_id': '186338',
            'coordinates': [51.5074, -0.1278]
        }
    }

CITIES = load_cities_from_csv('cities.csv')

# --- External API Functions ---

def get_booking_location_id(city_query):
    """Get Booking.com location ID with error handling."""
    if not city_query: 
        return None
    
    url = f"https://{BOOKING_API_HOST}/stays/auto-complete"
    params = {"query": city_query}
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and isinstance(data.get('data'), list) and data['data']:
            location_id = data['data'][0].get('id')
            logging.info(f"✅ Booking.com location ID: {location_id} for query: {city_query}")
            return location_id
    except Exception as e:
        logging.error(f"❌ Failed to get Booking.com location ID: {e}")
    
    return None

def search_booking_hotels(location_id, checkin, checkout, adults, rooms):
    """Search Booking.com hotels with error handling."""
    url = f"https://{BOOKING_API_HOST}/stays/search"
    params = {
        "locationId": location_id,
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "adults": adults,
        "rooms": rooms,
        "currency": "EUR"
    }
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        logging.info(f"✅ Booking.com: Found {len(data.get('data', []))} hotels")
        return data
    except Exception as e:
        logging.error(f"❌ Booking.com API error: {e}")
        return None

def search_tripadvisor_hotels(location_id, limit=15):
    """FIXED: Search TripAdvisor hotels with correct endpoint."""
    if not location_id:
        return None
    
    url = f"https://{TRIPADVISOR_API_HOST}/hotels/list"  # FIXED: Correct endpoint
    params = {
        "location_id": location_id,  # FIXED: Correct parameter name
        "limit": str(limit),
        "sort": "recommended",
        "offset": "0",
        "currency": "EUR",
        "lang": "en_US"
    }
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            hotels = data['data']
            logging.info(f"✅ TripAdvisor: Found {len(hotels)} hotels")
            return data
        else:
            logging.warning(f"⚠️ TripAdvisor: Unexpected data structure: {data}")
            return None
            
    except Exception as e:
        logging.error(f"❌ TripAdvisor API error: {e}")
        return None

# --- URL & Data Processing Functions ---

def create_booking_url(hotel, city_info, params):
    """Enhanced Booking.com URL creation."""
    country_code_map = {
        'gb': 'en-gb', 'se': 'sv', 'fr': 'fr', 'es': 'es', 
        'it': 'it', 'de': 'de', 'nl': 'nl', 'dk': 'dk'
    }
    country = city_info.get('country', 'com')
    domain_suffix = country_code_map.get(country, 'com') + '.html'
    
    hotel_name = hotel.get('name', 'Hotel')
    hotel_id = hotel.get('id', '')
    
    base_params = {
        'ss': hotel_name,
        'dest_id': hotel_id,
        'dest_type': 'hotel',
        'checkin': params['checkin'],
        'checkout': params['checkout'],
        'group_adults': params['adults'],
        'no_rooms': params['rooms'],
        'group_children': '0',
        'search_selected': 'true'
    }
    
    query_string = urlencode(base_params)
    return f"https://www.booking.com/searchresults.{domain_suffix}?{query_string}"

def create_tripadvisor_url(hotel, city_info, params):
    """ENHANCED: Create TripAdvisor URL."""
    hotel_name = hotel.get('name', 'Hotel')
    hotel_id = hotel.get('location_id', '')
    city_tripadvisor_id = city_info.get('tripadvisor_id', '')
    
    if hotel_id and city_tripadvisor_id:
        # Direct hotel URL with booking parameters
        base_url = f"https://www.tripadvisor.com/Hotel_Review-g{city_tripadvisor_id}-d{hotel_id}"
        
        params_dict = {
            'checkin': params['checkin'],
            'checkout': params['checkout'],
            'adults': params['adults'],
            'rooms': '1'
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params_dict.items()])
        return f"{base_url}?{param_string}"
    
    # Fallback: Search URL
    search_query = quote_plus(f"{hotel_name} {city_info['name']}")
    return f"https://www.tripadvisor.com/Search?q={search_query}"

def process_booking_hotels(api_data, search_params, city_info):
    """Process Booking.com hotel data."""
    processed = []
    hotels_data = api_data.get('data', []) if api_data else []
    
    if not isinstance(hotels_data, list):
        return []
    
    for i, hotel in enumerate(hotels_data[:BOOKING_HOTEL_LIMIT]):
        # Price calculation
        price = 'N/A'
        if price_info := hotel.get('priceBreakdown', {}).get('grossPrice', {}).get('value'):
            try:
                nights = (datetime.strptime(search_params['checkout'], '%Y-%m-%d') - 
                         datetime.strptime(search_params['checkin'], '%Y-%m-%d')).days
                price = f"€{int(price_info / nights) if nights > 0 else int(price_info)}"
            except:
                price = f"€{int(price_info)}"
        
        # Coordinates
        coordinates = [
            float(hotel.get('latitude', city_info['coordinates'][0])),
            float(hotel.get('longitude', city_info['coordinates'][1]))
        ]
        
        processed.append({
            'id': hotel.get('id', f'booking_{i}'),
            'name': hotel.get('name', 'Unknown Hotel'),
            'address': hotel.get('address', city_info['name']),
            'coordinates': coordinates,
            'price': price,
            'rating': round(float(hotel.get('reviewScore', 0.0)) / 2, 1),
            'source': 'booking.com',
            'booking_url': create_booking_url(hotel, city_info, search_params),
            'tripadvisor_url': None  # Will be added if TripAdvisor data available
        })
    
    return processed

def process_tripadvisor_hotels(api_data, city_info, search_params):
    """ENHANCED: Process TripAdvisor hotel data."""
    processed = []
    hotels_data = api_data.get('data', []) if api_data else []
    
    if not isinstance(hotels_data, list):
        return []
    
    for i, hotel in enumerate(hotels_data[:TRIPADVISOR_HOTEL_LIMIT]):
        # Price extraction (TripAdvisor format)
        price = 'Price on request'
        if price_data := hotel.get('price'):
            if isinstance(price_data, dict):
                if 'display_price' in price_data:
                    price = price_data['display_price']
                elif 'amount' in price_data:
                    price = f"€{price_data['amount']}"
            elif isinstance(price_data, str):
                price = price_data
        
        # Coordinates
        coordinates = [
            float(hotel.get('latitude', city_info['coordinates'][0])),
            float(hotel.get('longitude', city_info['coordinates'][1]))
        ]
        
        # Reviews count
        reviews_count = int(hotel.get('num_reviews', 0))
        
        processed.append({
            'id': hotel.get('location_id', f'tripadvisor_{i}'),
            'name': hotel.get('name', 'Unknown Hotel'),
            'address': hotel.get('address', city_info['name']),
            'coordinates': coordinates,
            'price': price,
            'rating': float(hotel.get('rating', 4.0)),
            'reviews_count': reviews_count,
            'source': 'tripadvisor',
            'booking_url': None,  # TripAdvisor doesn't provide booking URLs
            'tripadvisor_url': create_tripadvisor_url(hotel, city_info, search_params)
        })
    
    return processed

def generate_mock_hotels(city_key, city_info, search_params):
    """Generate mock hotels when APIs fail."""
    mock_templates = MOCK_HOTELS.get(city_key, MOCK_HOTELS['stockholm'])
    
    mock_hotels = []
    for i, template in enumerate(mock_templates):
        mock_hotels.append({
            'id': f'mock_{city_key}_{i}',
            'name': template['name'],
            'address': city_info['name'],
            'coordinates': city_info['coordinates'],
            'price': f"€{template['price']}",
            'rating': template['rating'],
            'reviews_count': template.get('reviews', 0),
            'source': 'mock_data',
            'booking_url': f"https://www.booking.com/searchresults.html?ss={quote_plus(template['name'])}",
            'tripadvisor_url': f"https://www.tripadvisor.com/Search?q={quote_plus(template['name'])}"
        })
    
    return mock_hotels

# --- Enhanced API Route Handlers ---

def handle_hotel_search(source):
    """Enhanced hotel search with better error handling."""
    today = datetime.now()
    params = {
        'city_key': request.args.get('city', 'stockholm').lower(),
        'checkin': request.args.get('checkin', (today + timedelta(days=1)).strftime('%Y-%m-%d')),
        'checkout': request.args.get('checkout', (today + timedelta(days=2)).strftime('%Y-%m-%d')),
        'adults': request.args.get('adults', '2'),
        'rooms': request.args.get('rooms', '1')
    }
    
    if params['city_key'] not in CITIES:
        return jsonify({
            'error': f"City '{params['city_key']}' not supported",
            'available_cities': list(CITIES.keys())
        }), 400
    
    city_info = CITIES[params['city_key']]
    city_name = city_info['name']
    
    try:
        logging.info(f"Handling '{source}' search for '{city_name}'.")
        processed_hotels = []

        if source == 'booking':
            location_id = get_booking_location_id(city_info['search_query'])
            if location_id:
                api_data = search_booking_hotels(location_id, params['checkin'], params['checkout'], params['adults'], params['rooms'])
                if api_data:
                    processed_hotels = process_booking_hotels(api_data, params, city_info)

        elif source == 'tripadvisor':
            tripadvisor_id = city_info.get('tripadvisor_id')
            if tripadvisor_id:
                api_data = search_tripadvisor_hotels(tripadvisor_id)
                if api_data:
                    processed_hotels = process_tripadvisor_hotels(api_data, city_info, params)

        # Fallback to mock data if no hotels found
        if not processed_hotels:
            processed_hotels = generate_mock_hotels(params['city_key'], city_info, params)
            logging.warning(f"Using mock data for {city_name} from {source}")
        
    except RequestException as e:
        status_code = e.response.status_code if e.response is not None else 500
        logging.error(f"API call to '{source}' failed with status {status_code}: {e}")
        
        # Return mock data on API failure
        processed_hotels = generate_mock_hotels(params['city_key'], city_info, params)
        
        return jsonify({
            'city': city_name,
            'hotels': processed_hotels,
            'total_found': len(processed_hotels),
            'search_params': params,
            'data_source': 'mock_data',
            'note': f"API error - using mock data. Status: {status_code}"
        })
    
    except Exception as e:
        logging.critical(f"Unhandled exception for source '{source}': {e}", exc_info=True)
        processed_hotels = generate_mock_hotels(params['city_key'], city_info, params)
        
        return jsonify({
            'city': city_name,
            'hotels': processed_hotels,
            'total_found': len(processed_hotels),
            'search_params': params,
            'data_source': 'mock_data',
            'note': 'Internal error - using mock data'
        }), 500

    return jsonify({
        'city': city_name,
        'hotels': processed_hotels,
        'total_found': len(processed_hotels),
        'search_params': params,
        'data_source': source
    })

def handle_dual_hotel_search():
    """NEW: Combined search from both Booking.com AND TripAdvisor."""
    today = datetime.now()
    params = {
        'city_key': request.args.get('city', 'stockholm').lower(),
        'checkin': request.args.get('checkin', (today + timedelta(days=1)).strftime('%Y-%m-%d')),
        'checkout': request.args.get('checkout', (today + timedelta(days=2)).strftime('%Y-%m-%d')),
        'adults': request.args.get('adults', '2'),
        'rooms': request.args.get('rooms', '1')
    }
    
    if params['city_key'] not in CITIES:
        return jsonify({
            'error': f"City '{params['city_key']}' not supported",
            'available_cities': list(CITIES.keys())
        }), 400
    
    city_info = CITIES[params['city_key']]
    city_name = city_info['name']
    
    booking_hotels = []
    tripadvisor_hotels = []
    
    # Search Booking.com
    try:
        location_id = get_booking_location_id(city_info['search_query'])
        if location_id:
            booking_data = search_booking_hotels(location_id, params['checkin'], params['checkout'], params['adults'], params['rooms'])
            if booking_data:
                booking_hotels = process_booking_hotels(booking_data, params, city_info)
    except Exception as e:
        logging.error(f"Booking.com search failed: {e}")
    
    # Search TripAdvisor
    try:
        tripadvisor_id = city_info.get('tripadvisor_id')
        if tripadvisor_id:
            tripadvisor_data = search_tripadvisor_hotels(tripadvisor_id)
            if tripadvisor_data:
                tripadvisor_hotels = process_tripadvisor_hotels(tripadvisor_data, city_info, params)
    except Exception as e:
        logging.error(f"TripAdvisor search failed: {e}")
    
    # Combine results or use mock data
    all_hotels = []
    
    if booking_hotels or tripadvisor_hotels:
        # Add Booking.com hotels with TripAdvisor URLs if possible
        for booking_hotel in booking_hotels[:10]:
            # Try to find matching TripAdvisor hotel
            for ta_hotel in tripadvisor_hotels:
                if booking_hotel['name'].lower() in ta_hotel['name'].lower() or ta_hotel['name'].lower() in booking_hotel['name'].lower():
                    booking_hotel['tripadvisor_url'] = ta_hotel['tripadvisor_url']
                    booking_hotel['reviews_count'] = ta_hotel.get('reviews_count', 0)
                    break
            all_hotels.append(booking_hotel)
        
        # Add remaining TripAdvisor hotels
        for ta_hotel in tripadvisor_hotels[:5]:
            if not any(hotel['name'].lower() in ta_hotel['name'].lower() for hotel in all_hotels):
                all_hotels.append(ta_hotel)
    else:
        # Use mock data if both APIs fail
        all_hotels = generate_mock_hotels(params['city_key'], city_info, params)
    
    return jsonify({
        'city': city_name,
        'hotels': all_hotels,
        'total_found': len(all_hotels),
        'search_params': params,
        'data_sources': ['booking.com', 'tripadvisor'],
        'booking_count': len(booking_hotels),
        'tripadvisor_count': len(tripadvisor_hotels)
    })

# --- Flask Routes ---
@app.route('/')
def home():
    return render_template_string('''
    <h1>🏨 STAYFINDR Backend v10.0</h1>
    <p>Enhanced with dual API integration and smart fallbacks</p>
    <h3>Endpoints:</h3>
    <ul>
        <li><a href="/api/hotels/booking?city=stockholm">/api/hotels/booking</a> - Booking.com only</li>
        <li><a href="/api/hotels/tripadvisor?city=stockholm">/api/hotels/tripadvisor</a> - TripAdvisor only</li>
        <li><a href="/api/hotels/dual?city=stockholm">/api/hotels/dual</a> - BOTH sources combined</li>
        <li><a href="/api/cities">/api/cities</a> - Available cities</li>
        <li><a href="/test">/test</a> - Health check</li>
    </ul>
    <p><strong>New in v10.0:</strong> Fixed TripAdvisor API, added dual endpoint, mock data fallback</p>
    ''')

@app.route('/api/cities')
def get_cities_route():
    return jsonify({'cities': CITIES, 'total': len(CITIES)})

@app.route('/api/room-types')
def get_room_types_route():
    room_types = {
        'single': {'name': 'Single Room', 'guests': 1},
        'double': {'name': 'Double Room', 'guests': 2},
        'family': {'name': 'Family Room', 'guests': 4},
        'junior_suite': {'name': 'Junior Suite', 'guests': 2},
        'suite': {'name': 'Suite/Apartment', 'guests': 3}
    }
    return jsonify({'room_types': room_types})

@app.route('/api/hotels/booking')
def get_booking_hotels_route():
    return handle_hotel_search(source='booking')

@app.route('/api/hotels/tripadvisor')
def get_tripadvisor_hotels_route():
    return handle_hotel_search(source='tripadvisor')

@app.route('/api/hotels/dual')  # NEW: Dual endpoint
def get_dual_hotels_route():
    return handle_dual_hotel_search()

@app.route('/test')
def test_endpoint_route():
    return jsonify({
        'status': 'STAYFINDR Backend v10.0 Active',
        'features': ['dual_api', 'mock_fallback', 'enhanced_urls'],
        'endpoints': ['/api/hotels/booking', '/api/hotels/tripadvisor', '/api/hotels/dual'],
        'cities_loaded': len(CITIES)
    })

# --- Application Startup ---
if __name__ == '__main__':
    logging.info("🚀 Starting STAYFINDR Backend v10.0...")
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not is_production, host='0.0.0.0', port=port)
