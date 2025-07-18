# STAYFINDR BACKEND v12.2 - Final & Stable Version
# FINAL FIX: Corrected the extraction path for TripAdvisor's 'contentId'.
# The previous version was looking in the wrong place, causing the two-step search to fail.
# This version uses the correct, deeply-nested path, which is the definitive fix.

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode
import re
import csv
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
TRIPADVISOR_API_HOST = "tripadvisor-com1.p.rapidapi.com"
BOOKING_HOTEL_LIMIT = 20
TRIPADVISOR_HOTEL_LIMIT = 15
URL_REGEX = re.compile(r'\d+')

# --- Data Loading ---
def load_cities_from_csv(filename='cities.csv'):
    """Loads cities from CSV. Only key, name, search_query, and country are needed."""
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

def get_tripadvisor_geo_id(city_name):
    """Step 1 (TripAdvisor): Dynamically fetches the Geo ID."""
    url = f"https://{TRIPADVISOR_API_HOST}/locations/search"
    params = {"query": city_name, "lang": "en_US"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get('data'):
        for item in data['data']:
            if item.get('result_type') == 'geography':
                if geo_id := item.get('result_object', {}).get('location_id'):
                    return geo_id
    return None

def search_tripadvisor_hotels_list(geo_id):
    """Step 2 (TripAdvisor): Get a list of hotels to find their contentIds and coordinates."""
    if not geo_id: return []
    url = f"https://{TRIPADVISOR_API_HOST}/hotels/search"
    params = {"geoId": geo_id, "lang": "en_US"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get('data', [])

def get_tripadvisor_hotel_offers(content_id, checkin, checkout, adults):
    """Step 3 (TripAdvisor): Get pricing/offers for a specific hotel."""
    url = f"https://{TRIPADVISOR_API_HOST}/hotels/offers"
    params = {"contentId": content_id, "checkIn": checkin, "checkOut": checkout, "adults": adults, "currencyCode": "EUR"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=10)
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

def process_tripadvisor_hotel(hotel_summary, offers_data):
    """Combines hotel summary data with its specific offer data."""
    lowest_price_offer = min(offers_data.get('data', []), key=lambda x: x.get('price', float('inf')), default=None)
    if not lowest_price_offer: return None
    
    price_str = lowest_price_offer.get('price')
    price = 'N/A'
    if price_str:
        numbers = re.findall(r'\d+', price_str.replace(',', ''))
        if numbers:
            price = int(numbers[0])

    return {
        'id': hotel_summary.get('id'), 'name': hotel_summary.get('title', 'Unknown Hotel'),
        'address': hotel_summary.get('secondaryInfo', 'N/A'),
        'coordinates': [float(hotel_summary.get('geoSummary', {}).get('latitude', 0)), float(hotel_summary.get('geoSummary', {}).get('longitude', 0))],
        'price': price,
        'rating': float(hotel_summary.get('bubbleRating', {}).get('rating', 4.0)),
        'source': 'tripadvisor',
        'booking_url': lowest_price_offer.get('url')
    }

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
        geo_id = get_tripadvisor_geo_id(city_info['name'])
        if not geo_id: return []
        
        hotel_list = search_tripadvisor_hotels_list(geo_id)
        processed_hotels = []
        for hotel_summary in hotel_list[:TRIPADVISOR_HOTEL_LIMIT]:
            # KORRIGERING: Använder den korrekta, djupt nästlade sökvägen för att hitta contentId.
            content_id = hotel_summary.get('cardLink', {}).get('route', {}).get('typedParams', {}).get('contentId')
            if not content_id:
                logging.warning(f"Could not find contentId for hotel: {hotel_summary.get('title')}")
                continue
            try:
                offers_data = get_tripadvisor_hotel_offers(content_id, params['checkin'], params['checkout'], params['adults'])
                full_hotel_data = process_tripadvisor_hotel(hotel_summary, offers_data)
                if full_hotel_data:
                    processed_hotels.append(full_hotel_data)
            except RequestException as offer_error:
                logging.warning(f"Could not fetch offers for TripAdvisor hotel {content_id}: {offer_error}")
                continue
        return processed_hotels
    except Exception as e:
        logging.error(f"Exception in fetch_tripadvisor_hotels_helper: {e}")
        return []

# --- Flask Routes ---
@app.route('/')
def home(): return render_template_string('<h1>STAYFINDR Backend v12.2</h1><p>Final and stable version.</p>')

@app.route('/api/cities')
def get_cities_route(): return jsonify({'cities': CITIES})

@app.route('/api/room-types')
def get_room_types_route():
    room_types = {'single': {'name': 'Single Room'}, 'double': {'name': 'Double Room'}, 'family': {'name': 'Family Room'}}
    return jsonify({'room_types': room_types})

def handle_single_source_search(source, params, city_info):
    """Handles a search for a single, isolated source."""
    if source == 'booking':
        return fetch_booking_hotels_helper(city_info, params)
    elif source == 'tripadvisor':
        return fetch_tripadvisor_hotels_helper(city_info, params)
    return []

@app.route('/api/hotels/booking')
def get_booking_hotels_route():
    today = datetime.now()
    params = {'city_key': request.args.get('city', 'stockholm').lower(), 'checkin': request.args.get('checkin', (today + timedelta(days=1)).strftime('%Y-%m-%d')), 'checkout': request.args.get('checkout', (today + timedelta(days=2)).strftime('%Y-%m-%d')), 'adults': request.args.get('adults', '2'), 'rooms': request.args.get('rooms', '1')}
    if params['city_key'] not in CITIES: return jsonify({'error': f"City '{params['city_key']}' not supported"}), 400
    city_info = CITIES[params['city_key']]
    processed_hotels = handle_single_source_search('booking', params, city_info)
    return jsonify({'city': city_info['name'], 'hotels': processed_hotels, 'total_found': len(processed_hotels), 'search_params': params})

@app.route('/api/hotels/tripadvisor')
def get_tripadvisor_hotels_route():
    today = datetime.now()
    params = {'city_key': request.args.get('city', 'stockholm').lower(), 'checkin': request.args.get('checkin', (today + timedelta(days=1)).strftime('%Y-%m-%d')), 'checkout': request.args.get('checkout', (today + timedelta(days=2)).strftime('%Y-%m-%d')), 'adults': request.args.get('adults', '2'), 'rooms': request.args.get('rooms', '1')}
    if params['city_key'] not in CITIES: return jsonify({'error': f"City '{params['city_key']}' not supported"}), 400
    city_info = CITIES[params['city_key']]
    processed_hotels = handle_single_source_search('tripadvisor', params, city_info)
    return jsonify({'city': city_info['name'], 'hotels': processed_hotels, 'total_found': len(processed_hotels), 'search_params': params})

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
def test_endpoint_route(): return jsonify({'status': 'STAYFINDR Backend v12.2 Active'})

# --- Application Startup ---
if __name__ == '__main__':
    logging.info("🚀 Starting STAYFINDR Backend v12.2...")
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not is_production, host='0.0.0.0', port=port)
