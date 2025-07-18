# STAYFINDR BACKEND v11.7 - Final Corrected Logic
# FINAL VERSION: This version is a complete rewrite of the TripAdvisor logic to match the user-provided API response.
# - Uses the correct, legacy API host (tripadvisor16.p.rapidapi.com).
# - Correctly parses the new, complex data structure for hotel details, including price and booking URL.
# - Retains the stable, intelligent search for Booking.com.

import os
import logging
import csv
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode
import re
from concurrent.futures import ThreadPoolExecutor

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
TRIPADVISOR_API_HOST = "tripadvisor16.p.rapidapi.com" # Using the confirmed working host
BOOKING_HOTEL_LIMIT = 20
TRIPADVISOR_HOTEL_LIMIT = 15
URL_REGEX = re.compile(r'\d+')

# --- Data Loading ---
def load_cities_from_csv(filename='cities.csv'):
    """Loads cities from CSV, ensuring all necessary fields are present."""
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
                    'country': row.get('country', 'com').lower(),
                    'tripadvisor_id': row.get('tripadvisor_id', '')
                }
        logging.info(f"Successfully loaded {len(cities)} cities from {filename}.")
        return cities
    except FileNotFoundError:
        logging.error(f"CRITICAL: The file {filename} was not found.")
        return {}
    except Exception as e:
        logging.error(f"CRITICAL: Failed to read or parse {filename}. Error: {e}", exc_info=True)
        return {}

CITIES = load_cities_from_csv()

# --- External API Functions ---

def get_booking_location_id(city_query, country_code):
    """Intelligently fetches location ID by strictly matching the country code."""
    if not city_query: return None
    url = f"https://{BOOKING_API_HOST}/stays/auto-complete"
    params = {"query": city_query}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data and isinstance(data.get('data'), list):
        for result in data['data']:
            api_country_code = result.get('cc1', '')
            if isinstance(api_country_code, str) and api_country_code.lower() == country_code:
                return result.get('id')
    return None

def search_booking_hotels(location_id, checkin, checkout, adults, rooms):
    url = f"https://{BOOKING_API_HOST}/stays/search"
    params = {"locationId": location_id, "checkinDate": checkin, "checkoutDate": checkout, "adults": adults, "rooms": rooms, "currency": "EUR"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params=params, timeout=15)
    response.raise_for_status()
    return response.json()

def search_tripadvisor_hotels(geo_id, checkin, checkout, adults):
    """Searches TripAdvisor using the confirmed working legacy endpoint."""
    if not geo_id: return None
    url = f"https://{TRIPADVISOR_API_HOST}/api/v1/hotels/searchHotels"
    params = {"geoId": geo_id, "checkIn": checkin, "checkOut": checkout, "adults": adults, "rooms": "1", "currencyCode": "EUR"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=15)
    response.raise_for_status()
    return response.json()

# --- URL & Data Processing Functions ---

def create_booking_url(hotel, city_info, params):
    country_code_map = {'gb': 'en-gb', 'se': 'sv', 'fr': 'fr', 'es': 'es', 'it': 'it', 'de': 'de', 'nl': 'nl'}
    country = city_info.get('country', 'com')
    domain_suffix = country_code_map.get(country, 'com') + '.html'
    base_params = {'ss': hotel.get('name', 'Hotel'), 'checkin': params['checkin'], 'checkout': params['checkout'], 'group_adults': params['adults'], 'no_rooms': params['rooms'], 'group_children': '0'}
    query_string = urlencode(base_params)
    return f"https://www.booking.com/searchresults.{domain_suffix}?{query_string}"

def process_booking_hotels(api_data, search_params, city_info):
    processed = []
    hotels_data = api_data.get('data', []) if api_data else []
    if not isinstance(hotels_data, list): return []
    for hotel in hotels_data[:BOOKING_HOTEL_LIMIT]:
        price = 'N/A'
        if price_info := hotel.get('priceBreakdown', {}).get('grossPrice', {}).get('value'):
            nights = (datetime.strptime(search_params['checkout'], '%Y-%m-%d') - datetime.strptime(search_params['checkin'], '%Y-%m-%d')).days
            price = int(price_info / nights) if nights > 0 else int(price_info)
        processed.append({
            'id': hotel.get('id'), 'name': hotel.get('name', 'Unknown Hotel'),
            'address': hotel.get('address', 'N/A'),
            'coordinates': [float(hotel.get('latitude', 0)), float(hotel.get('longitude', 0))],
            'price': price, 'rating': round(float(hotel.get('reviewScore', 0.0)) / 2, 1),
            'source': 'booking.com',
            'booking_url': create_booking_url(hotel, city_info, search_params)
        })
    return processed

def process_tripadvisor_hotels(api_data):
    """Processes the complex TripAdvisor response structure."""
    processed = []
    # The actual list of hotels is nested under data -> data
    hotels_data = api_data.get('data', {}).get('data', []) if api_data else []
    if not isinstance(hotels_data, list): return []

    for hotel in hotels_data[:TRIPADVISOR_HOTEL_LIMIT]:
        price = 'N/A'
        if price_str := hotel.get('priceForDisplay'):
            # Price can be a simple string like "$123"
            numbers = URL_REGEX.findall(str(price_str).replace(',', ''))
            if numbers:
                price = int(numbers[0])
        
        booking_url = hotel.get('commerceInfo', {}).get('externalUrl', '#')

        processed.append({
            'id': hotel.get('id'), 'name': hotel.get('title', 'Unknown Hotel'),
            'address': hotel.get('secondaryInfo', 'N/A'),
            'coordinates': [0.0, 0.0], # Coordinates are not in this response, would need another call
            'price': price, 'rating': float(hotel.get('bubbleRating', {}).get('rating', 4.0)),
            'source': 'tripadvisor',
            'booking_url': booking_url
        })
    return processed

# --- Helper Functions for Parallel Execution ---

def fetch_booking_hotels_helper(city_info, params):
    try:
        location_id = get_booking_location_id(city_info['search_query'], city_info['country'])
        if not location_id: return []
        api_data = search_booking_hotels(location_id, params['checkin'], params['checkout'], params['adults'], params['rooms'])
        return process_booking_hotels(api_data, params, city_info)
    except Exception as e:
        logging.error(f"Exception in fetch_booking_hotels_helper: {e}")
        return []

def fetch_tripadvisor_hotels_helper(city_info, params):
    try:
        geo_id = city_info.get('tripadvisor_id')
        if not geo_id: return []
        api_data = search_tripadvisor_hotels(geo_id, params['checkin'], params['checkout'], params['adults'])
        return process_tripadvisor_hotels(api_data)
    except Exception as e:
        logging.error(f"Exception in fetch_tripadvisor_hotels_helper: {e}")
        return []

# --- Flask Routes ---
@app.route('/')
def home(): return render_template_string('<h1>STAYFINDR Backend v11.7</h1><p>Final corrected logic.</p>')

@app.route('/api/cities')
def get_cities_route(): return jsonify({'cities': CITIES})

@app.route('/api/room-types')
def get_room_types_route():
    room_types = {'single': {'name': 'Single Room'}, 'double': {'name': 'Double Room'}, 'family': {'name': 'Family Room'}}
    return jsonify({'room_types': room_types})

@app.route('/api/hotels/booking')
def get_booking_hotels_route():
    return handle_single_source_search(source='booking')

@app.route('/api/hotels/tripadvisor')
def get_tripadvisor_hotels_route():
    return handle_single_source_search(source='tripadvisor')

def handle_single_source_search(source):
    """Handles requests for a single data source."""
    today = datetime.now()
    params = {'city_key': request.args.get('city', 'stockholm').lower(), 'checkin': request.args.get('checkin', (today + timedelta(days=1)).strftime('%Y-%m-%d')), 'checkout': request.args.get('checkout', (today + timedelta(days=2)).strftime('%Y-%m-%d')), 'adults': request.args.get('adults', '2'), 'rooms': request.args.get('rooms', '1')}
    if params['city_key'] not in CITIES: return jsonify({'error': f"City '{params['city_key']}' not supported"}), 400
    
    city_info = CITIES[params['city_key']]
    city_name = city_info['name']
    
    try:
        if source == 'booking':
            processed_hotels = fetch_booking_hotels_helper(city_info, params)
        elif source == 'tripadvisor':
            processed_hotels = fetch_tripadvisor_hotels_helper(city_info, params)
        else:
            return jsonify({'error': "Invalid source"}), 400
            
    except Exception as e:
        logging.critical(f"An unhandled exception occurred for source '{source}': {e}", exc_info=True)
        return jsonify({'error': 'Ett oväntat internt fel uppstod.'}), 500

    return jsonify({'city': city_name, 'hotels': processed_hotels, 'total_found': len(processed_hotels), 'search_params': params})

@app.route('/api/hotels/dual')
def get_dual_hotels():
    """Get hotels from BOTH Booking.com and TripAdvisor in parallel."""
    today = datetime.now()
    params = {'city_key': request.args.get('city', 'stockholm').lower(), 'checkin': request.args.get('checkin', (today + timedelta(days=1)).strftime('%Y-%m-%d')), 'checkout': request.args.get('checkout', (today + timedelta(days=2)).strftime('%Y-%m-%d')), 'adults': request.args.get('adults', '2'), 'rooms': request.args.get('rooms', '1')}
    if params['city_key'] not in CITIES: return jsonify({'error': f"City '{params['city_key']}' not supported"}), 400
    
    city_info = CITIES[params['city_key']]
    all_hotels = []
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        booking_future = executor.submit(fetch_booking_hotels_helper, city_info, params)
        tripadvisor_future = executor.submit(fetch_tripadvisor_hotels_helper, city_info, params)
        
        booking_hotels = booking_future.result()
        tripadvisor_hotels = tripadvisor_future.result()
        
        all_hotels.extend(booking_hotels)
        all_hotels.extend(tripadvisor_hotels)

    all_hotels.sort(key=lambda x: x.get('rating', 0), reverse=True)
    
    return jsonify({
        'city': city_info['name'],
        'hotels': all_hotels,
        'total_found': len(all_hotels),
        'search_params': params,
        'data_source': 'dual'
    })

@app.route('/test')
def test_endpoint_route(): return jsonify({'status': 'STAYFINDR Backend v11.7 Active'})

# --- Application Startup ---
if __name__ == '__main__':
    logging.info("🚀 Starting STAYFINDR Backend v11.7...")
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not is_production, host='0.0.0.0', port=port)# STAYFINDR BACKEND v11.0 - Dual API Integration
# Flask backend with Booking.com + TripAdvisor integration
# FIXED: Real TripAdvisor data + 71 cities from CSV

import os
import logging
import csv
from datetime import datetime
from urllib.parse import quote_plus
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
import threading

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RapidAPI Configuration
RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
BOOKING_HOST = "booking-com18.p.rapidapi.com"
TRIPADVISOR_HOST = "tripadvisor16.p.rapidapi.com"

# Cache for TripAdvisor location IDs (to avoid repeated API calls)
TRIPADVISOR_LOCATION_CACHE = {}
cache_lock = threading.Lock()

# Country codes for Booking.com URLs
COUNTRY_CODES = {
    'stockholm': 'sv', 'gothenburg': 'sv', 'malmo': 'sv',
    'oslo': 'no', 'bergen': 'no',
    'helsinki': 'fi', 'tampere': 'fi',
    'copenhagen': 'dk', 'aarhus': 'dk',
    'paris': 'fr', 'lyon': 'fr', 'nice': 'fr', 'marseille': 'fr', 'bordeaux': 'fr',
    'london': 'en-gb', 'edinburgh': 'en-gb', 'manchester': 'en-gb', 'liverpool': 'en-gb',
    'amsterdam': 'nl', 'rotterdam': 'nl', 'utrecht': 'nl',
    'brussels': 'nl', 'antwerp': 'nl',
    'barcelona': 'es', 'madrid': 'es', 'palma': 'es', 'ibiza': 'es', 
    'valencia': 'es', 'seville': 'es', 'bilbao': 'es',
    'rome': 'it', 'milan': 'it', 'florence': 'it', 'venice': 'it', 'naples': 'it',
    'berlin': 'de', 'munich': 'de', 'hamburg': 'de', 'cologne': 'de', 'frankfurt': 'de',
    'vienna': 'de', 'salzburg': 'de',
    'zurich': 'de', 'geneva': 'fr', 'bern': 'de',
    'prague': 'cs', 'brno': 'cs',
    'warsaw': 'pl', 'krakow': 'pl',
    'budapest': 'hu', 'debrecen': 'hu',
    'dublin': 'en-gb', 'cork': 'en-gb',
    'lisbon': 'pt', 'porto': 'pt',
    'athens': 'el', 'santorini': 'el', 'mykonos': 'el', 'thessaloniki': 'el'
}

def load_cities_from_csv():
    """Load all cities from cities.csv file"""
    cities = {}
    csv_path = 'cities.csv'
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ cities.csv not found at {csv_path}")
        return get_fallback_cities()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                city_key = row.get('key', '').lower().strip()
                if city_key:
                    cities[city_key] = {
                        'name': row.get('name', '').strip(),
                        'coordinates': [
                            float(row.get('lat', 0)),
                            float(row.get('lon', 0))
                        ],
                        'search_query': row.get('search_query', '').strip(),
                        'country': row.get('country', '').strip(),
                        'tripadvisor_id': row.get('tripadvisor_id', '').strip()
                    }
                    logger.info(f"✅ Loaded city: {city_key} - {cities[city_key]['name']}")
        
        logger.info(f"✅ Loaded {len(cities)} cities from cities.csv")
        return cities
        
    except Exception as e:
        logger.error(f"❌ Error reading cities.csv: {e}")
        return get_fallback_cities()

def get_fallback_cities():
    """Minimal fallback cities if CSV fails"""
    return {
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
        }
    }

# Load cities at startup
CITIES = load_cities_from_csv()

# === BOOKING.COM API FUNCTIONS ===

def get_booking_location_id(city_info):
    """Get Booking.com location ID for a city"""
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {"query": city_info['search_query'], "languageCode": "en"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": BOOKING_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                location_id = data['data'][0].get('id')
                logger.info(f"✅ Booking location_id: {location_id} for {city_info['name']}")
                return location_id
    except Exception as e:
        logger.error(f"❌ Booking location ID error: {e}")
    
    return None

def search_booking_hotels(location_id, checkin, checkout, adults, rooms):
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
        "x-rapidapi-host": BOOKING_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            return data
    except Exception as e:
        logger.error(f"❌ Booking hotels search error: {e}")
    
    return None

# === TRIPADVISOR API FUNCTIONS ===

# TRIPADVISOR FIX - Uppdaterade funktioner för Backend v11.1
# Ersätt dessa funktioner i din backend för att fixa Stockholm-problemet

def get_tripadvisor_location_id(city_info):
    """Get TripAdvisor location ID for a city - FIXED VERSION"""
    
    # Check cache first
    city_name = city_info['name']
    with cache_lock:
        if city_name in TRIPADVISOR_LOCATION_CACHE:
            logger.info(f"📦 Using cached TripAdvisor location ID for {city_name}")
            return TRIPADVISOR_LOCATION_CACHE[city_name]
    
    # Special handling for problematic cities
    special_location_ids = {
        'stockholm': '189852',  # Stockholm, Sweden
        'gothenburg': '189894',  # Gothenburg, Sweden
        'malmo': '189838',    # Malmö, Sweden
        'copenhagen': '189541', # Copenhagen, Denmark
        'oslo': '190479',      # Oslo, Norway
        'helsinki': '189934',  # Helsinki, Finland
        'paris': '187147',     # Paris, France
        'london': '186338',    # London, UK
        'barcelona': '187497', # Barcelona, Spain
        'madrid': '187514',    # Madrid, Spain
        'rome': '187791',      # Rome, Italy
        'berlin': '187323',    # Berlin, Germany
        'amsterdam': '188590', # Amsterdam, Netherlands
        'vienna': '190454',    # Vienna, Austria
        'prague': '274707',    # Prague, Czech Republic
    }
    
    # Check if we have a hardcoded location ID
    city_key = city_info['name'].split(',')[0].lower().replace(' ', '')
    if city_key in special_location_ids:
        location_id = special_location_ids[city_key]
        logger.info(f"✅ Using hardcoded TripAdvisor location_id: {location_id} for {city_name}")
        
        # Cache the result
        with cache_lock:
            TRIPADVISOR_LOCATION_CACHE[city_name] = location_id
        
        return location_id
    
    # Try API search with different query formats
    search_queries = [
        city_info['search_query'].split(',')[0],  # Just city name
        city_info['name'].split(',')[0],          # City from name field
        city_info.get('search_query', city_info['name'])  # Full search query
    ]
    
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchLocation"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": TRIPADVISOR_HOST
    }
    
    for query in search_queries:
        logger.info(f"🔍 Trying TripAdvisor location search with: {query}")
        
        querystring = {"query": query}
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    # Get the first result
                    location = data['data'][0]
                    location_id = location.get('geoId') or location.get('locationId')
                    
                    if location_id:
                        logger.info(f"✅ Found TripAdvisor location_id: {location_id} for {city_name}")
                        
                        # Cache the result
                        with cache_lock:
                            TRIPADVISOR_LOCATION_CACHE[city_name] = location_id
                        
                        return location_id
            else:
                logger.warning(f"TripAdvisor API returned {response.status_code} for query: {query}")
                
        except Exception as e:
            logger.error(f"TripAdvisor location search error for {query}: {e}")
            continue
    
    logger.error(f"❌ Could not find TripAdvisor location for {city_name}")
    return None


def search_tripadvisor_hotels(location_id, checkin, checkout, adults, rooms):
    """Search hotels using TripAdvisor API - IMPROVED VERSION"""
    
    # First try the standard endpoint
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchHotels"
    
    querystring = {
        "geoId": location_id,
        "checkIn": checkin,
        "checkOut": checkout,
        "pageNumber": "1",
        "currencyCode": "EUR",
        "adults": adults,
        "rooms": rooms
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": TRIPADVISOR_HOST
    }
    
    try:
        logger.info(f"🔍 Searching TripAdvisor hotels for location {location_id}")
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got hotels
            if data and 'data' in data:
                hotels_data = data.get('data', {})
                if isinstance(hotels_data, dict) and 'data' in hotels_data:
                    hotels = hotels_data['data']
                    logger.info(f"✅ Found {len(hotels)} hotels from TripAdvisor")
                    return data
                elif isinstance(hotels_data, list):
                    logger.info(f"✅ Found {len(hotels_data)} hotels from TripAdvisor")
                    return {'data': {'data': hotels_data}}
            
            # Try alternative response structure
            if 'result' in data and 'data' in data['result']:
                logger.info("Using alternative TripAdvisor response structure")
                return {'data': data['result']}
                
        elif response.status_code == 404:
            logger.error(f"TripAdvisor: No hotels found for location {location_id}")
        else:
            logger.error(f"TripAdvisor API returned {response.status_code}: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        logger.error("TripAdvisor API timeout")
    except Exception as e:
        logger.error(f"TripAdvisor hotels search error: {e}")
    
    return None

# Additional helper function to validate TripAdvisor responses
def validate_tripadvisor_response(data):
    """Validate and normalize TripAdvisor API response"""
    if not data:
        return None
    
    # Try different response structures
    hotels = None
    
    # Structure 1: data.data.data
    if 'data' in data and isinstance(data['data'], dict) and 'data' in data['data']:
        hotels = data['data']['data']
    # Structure 2: data.data (list)
    elif 'data' in data and isinstance(data['data'], list):
        hotels = data['data']
    # Structure 3: result.data
    elif 'result' in data and 'data' in data['result']:
        hotels = data['result']['data']
    
    if hotels and isinstance(hotels, list) and len(hotels) > 0:
        return hotels
    
    return None

def process_tripadvisor_hotels(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process TripAdvisor hotel data to match our format"""
    processed_hotels = []
    
    # Extract hotels from TripAdvisor response structure
    hotels = hotels_data.get('data', {}).get('data', [])
    
    for i, hotel in enumerate(hotels[:20]):  # Limit to 20 hotels
        try:
            # Extract hotel name
            hotel_name = hotel.get('title', 'Unknown Hotel')
            
            # Extract coordinates
            latitude = hotel.get('latitude')
            longitude = hotel.get('longitude')
            
            if latitude and longitude:
                coordinates = [float(latitude), float(longitude)]
            else:
                # Fallback to city center
                coordinates = city_info['coordinates']
            
            # Extract price
            price = 'N/A'
            price_details = hotel.get('priceDetails', {})
            if price_details:
                display_price = price_details.get('displayPrice', {})
                if isinstance(display_price, dict):
                    price_str = display_price.get('string', '')
                elif isinstance(display_price, str):
                    price_str = display_price
                else:
                    price_str = ''
                
                # Extract numeric price
                if price_str:
                    import re
                    numbers = re.findall(r'\d+', price_str.replace(',', ''))
                    if numbers:
                        price = int(numbers[0])
            
            # Extract rating
            rating = 4.0  # Default
            rating_info = hotel.get('bubbleRating', {})
            if rating_info:
                rating = float(rating_info.get('rating', 4.0))
            
            # Extract review count
            reviews_count = hotel.get('reviewCount', 0)
            
            # Build TripAdvisor URL
            hotel_id = hotel.get('id', '')
            tripadvisor_url = f"https://www.tripadvisor.com/Hotel_Review-g{hotel_id}.html"
            
            # Create booking search URL
            country_code = COUNTRY_CODES.get(city_key, 'en-gb')
            booking_url = f"https://www.booking.com/searchresults.{country_code}.html?ss={quote_plus(hotel_name)}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
            
            processed_hotel = {
                'id': f"ta_{hotel.get('id', i)}",
                'name': hotel_name,
                'address': hotel.get('address', city_info['name']),
                'coordinates': coordinates,
                'price': price,
                'rating': rating,
                'reviews_count': reviews_count,
                'booking_url': booking_url,
                'tripadvisor_url': tripadvisor_url,
                'source': 'tripadvisor',
                'provider_rank': hotel.get('rank', i + 1)
            }
            
            processed_hotels.append(processed_hotel)
            
        except Exception as e:
            logger.error(f"Error processing TripAdvisor hotel {i}: {e}")
            continue
    
    return processed_hotels

def create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key):
    """Create hotel booking URL"""
    # Get hotel name and ID
    hotel_id = hotel.get('id') or hotel.get('hotel_id')
    hotel_name = hotel.get('name', 'Hotel')
    
    # Get country code
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    
    # Create search URL with hotel name
    base_params = {
        'ss': hotel_name,
        'checkin': checkin,
        'checkout': checkout,
        'group_adults': adults,
        'no_rooms': rooms,
        'search_selected': 'true'
    }
    
    if hotel_id:
        base_params['dest_id'] = hotel_id
        base_params['dest_type'] = 'hotel'
    
    params_string = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in base_params.items()])
    
    return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"

def process_booking_hotels(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process Booking.com hotel data"""
    processed_hotels = []
    
    for i, hotel in enumerate(hotels_data):
        # Skip problematic Stockholm hotel in Germany
        hotel_name = hotel.get('name', 'Unknown Hotel')
        if city_key == 'stockholm' and 'stockholm' in hotel_name.lower() and len(hotel_name.split()) == 1:
            logger.warning(f"🔧 Filtering out German hotel 'Stockholm'")
            continue
        
        # Extract coordinates
        latitude = hotel.get('latitude')
        longitude = hotel.get('longitude')
        
        if latitude and longitude:
            coordinates = [float(latitude), float(longitude)]
        else:
            coordinates = city_info['coordinates']
        
        # Extract price
        price = 'N/A'
        if 'priceBreakdown' in hotel:
            price_info = hotel['priceBreakdown'].get('grossPrice', {})
            if 'value' in price_info:
                total_price = price_info['value']
                try:
                    checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
                    checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
                    nights = (checkout_date - checkin_date).days
                    if nights > 0:
                        price = int(total_price / nights)
                    else:
                        price = total_price
                except:
                    price = int(total_price / 7)
        
        # Extract rating
        rating = hotel.get('reviewScore', 4.0)
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)
        
        # Create booking URL
        booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key)
        
        processed_hotel = {
            'id': f"bk_{hotel.get('id', i)}",
            'name': hotel_name,
            'address': hotel.get('address', city_info['name']),
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'booking_url': booking_url,
            'source': 'booking',
            'provider_rank': i + 1
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels[:20]  # Limit to 20 hotels

# === API ENDPOINTS ===

@app.route('/')
def home():
    """API Documentation Page"""
    total_cities = len(CITIES)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Backend API v11.0</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .new { background: #d4edda; border-left: 4px solid #28a745; }
            .feature { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 8px; }
            .status { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ffc107; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API v11.0</h1>
        <p>Dual API Integration: Booking.com + TripAdvisor</p>
        
        <div class="status">
            <strong>🎯 v11.0 Features:</strong><br>
            ✅ Real TripAdvisor API integration (no more mock data!)<br>
            ✅ Parallel search from both Booking.com and TripAdvisor<br>
            ✅ {{total_cities}} European cities supported<br>
            ✅ Intelligent caching for better performance
        </div>
        
        <h2>API Endpoints:</h2>
        
        <div class="endpoint new">
            <strong>/api/hotels/dual</strong> - Get hotels from BOTH sources<br>
            Combines Booking.com + TripAdvisor results<br>
            <em>Returns up to 40 hotels (20 from each source)</em>
        </div>
        
        <div class="endpoint">
            <strong>/api/hotels/booking</strong> - Booking.com hotels only<br>
            Parameters: city, checkin, checkout, adults, rooms
        </div>
        
        <div class="endpoint">
            <strong>/api/hotels/tripadvisor</strong> - TripAdvisor hotels only<br>
            Parameters: city, checkin, checkout, adults, rooms
        </div>
        
        <div class="endpoint">
            <strong>/api/cities</strong> - List all {{total_cities}} cities
        </div>
        
        <div class="endpoint">
            <strong>/test</strong> - Test dual API with Stockholm
        </div>
        
        <div class="feature">
            <strong>Performance Features:</strong><br>
            • Location ID caching reduces API calls<br>
            • Parallel API requests for faster results<br>
            • Automatic fallback if one API fails
        </div>
    </body>
    </html>
    ''', total_cities=total_cities)

@app.route('/api/cities')
def get_cities():
    """Get all supported cities"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES),
        'source': 'cities.csv'
    })

@app.route('/api/hotels/booking')
def get_booking_hotels():
    """Get only Booking.com hotels"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-20')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    
    # Get Booking.com location ID
    location_id = get_booking_location_id(city_info)
    if not location_id:
        return jsonify({'error': f'Could not find Booking.com location for {city}'}), 404
    
    # Search hotels
    hotels_data = search_booking_hotels(location_id, checkin, checkout, adults, rooms)
    if not hotels_data or 'data' not in hotels_data:
        return jsonify({'error': 'No hotels found on Booking.com'}), 404
    
    # Process hotels
    processed_hotels = process_booking_hotels(
        hotels_data['data'][:20], 
        city_info, 
        checkin, 
        checkout, 
        adults, 
        rooms,
        city
    )
    
    return jsonify({
        'city': city_info['name'],
        'hotels': processed_hotels,
        'total_found': len(processed_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms
        },
        'data_source': 'booking'
    })

@app.route('/api/hotels/tripadvisor')
def get_tripadvisor_hotels():
    """Get only TripAdvisor hotels"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-20')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    
    # Get TripAdvisor location ID
    location_id = get_tripadvisor_location_id(city_info)
    if not location_id:
        return jsonify({'error': f'Could not find TripAdvisor location for {city}'}), 404
    
    # Search hotels
    hotels_data = search_tripadvisor_hotels(location_id, checkin, checkout, adults, rooms)
    if not hotels_data:
        return jsonify({'error': 'No hotels found on TripAdvisor'}), 404
    
    # Process hotels
    processed_hotels = process_tripadvisor_hotels(
        hotels_data, 
        city_info, 
        checkin, 
        checkout, 
        adults, 
        rooms,
        city
    )
    
    return jsonify({
        'city': city_info['name'],
        'hotels': processed_hotels,
        'total_found': len(processed_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms
        },
        'data_source': 'tripadvisor'
    })

@app.route('/api/hotels/dual')
def get_dual_hotels():
    """Get hotels from BOTH Booking.com and TripAdvisor"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-20')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    all_hotels = []
    errors = []
    
    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both API calls
        booking_future = executor.submit(
            fetch_booking_hotels, 
            city_info, city, checkin, checkout, adults, rooms
        )
        tripadvisor_future = executor.submit(
            fetch_tripadvisor_hotels,
            city_info, city, checkin, checkout, adults, rooms
        )
        
        # Get Booking.com results
        try:
            booking_hotels = booking_future.result(timeout=10)
            all_hotels.extend(booking_hotels)
            logger.info(f"✅ Got {len(booking_hotels)} hotels from Booking.com")
        except Exception as e:
            logger.error(f"❌ Booking.com error: {e}")
            errors.append(f"Booking.com: {str(e)}")
        
        # Get TripAdvisor results
        try:
            tripadvisor_hotels = tripadvisor_future.result(timeout=10)
            all_hotels.extend(tripadvisor_hotels)
            logger.info(f"✅ Got {len(tripadvisor_hotels)} hotels from TripAdvisor")
        except Exception as e:
            logger.error(f"❌ TripAdvisor error: {e}")
            errors.append(f"TripAdvisor: {str(e)}")
    
    # Sort by rating (best first)
    all_hotels.sort(key=lambda x: x.get('rating', 0), reverse=True)
    
    return jsonify({
        'city': city_info['name'],
        'hotels': all_hotels,
        'total_found': len(all_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms
        },
        'data_source': 'dual',
        'sources': {
            'booking': len([h for h in all_hotels if h['source'] == 'booking']),
            'tripadvisor': len([h for h in all_hotels if h['source'] == 'tripadvisor'])
        },
        'errors': errors if errors else None
    })

def fetch_booking_hotels(city_info, city_key, checkin, checkout, adults, rooms):
    """Helper function to fetch Booking.com hotels"""
    location_id = get_booking_location_id(city_info)
    if not location_id:
        raise Exception(f"No Booking.com location ID for {city_info['name']}")
    
    hotels_data = search_booking_hotels(location_id, checkin, checkout, adults, rooms)
    if not hotels_data or 'data' not in hotels_data:
        return []
    
    return process_booking_hotels(
        hotels_data['data'][:20],
        city_info,
        checkin,
        checkout,
        adults,
        rooms,
        city_key
    )

def fetch_tripadvisor_hotels(city_info, city_key, checkin, checkout, adults, rooms):
    """Helper function to fetch TripAdvisor hotels"""
    location_id = get_tripadvisor_location_id(city_info)
    if not location_id:
        raise Exception(f"No TripAdvisor location ID for {city_info['name']}")
    
    hotels_data = search_tripadvisor_hotels(location_id, checkin, checkout, adults, rooms)
    if not hotels_data:
        return []
    
    return process_tripadvisor_hotels(
        hotels_data,
        city_info,
        checkin,
        checkout,
        adults,
        rooms,
        city_key
    )

@app.route('/test')
def test_dual():
    """Test endpoint with Stockholm hotels from both sources"""
    return get_dual_hotels()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend v11.0...")
    print(f"📊 Loaded {len(CITIES)} cities from CSV")
    print("🔧 Dual API integration: Booking.com + TripAdvisor")
    print("✅ Real TripAdvisor data - no more mocks!")
    print("⚡ Parallel API calls for better performance")
    print("🌍 Ready to serve all European cities!")
    
    # Use PORT environment variable for deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
