# STAYFINDR BACKEND v5.4 - Final Version with Ultra-Robust Lines
# Contains final fixes for all copy-paste related SyntaxErrors.
# Complex one-liners have been rewritten into simpler multi-line blocks.

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode
from functools import cache
import re

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

CORS(app, origins=[
    "https://joa312.github.io",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:5000"
])

# --- API & Data Constants ---
BOOKING_API_HOST = "booking-com18.p.rapidapi.com"
TRIPADVISOR_API_HOST = "tripadvisor16.p.rapidapi.com"

URL_REGEX = re.compile(r'\d+')

ROOM_TYPES = {
    'single': {'name': 'Single Room', 'description': 'Perfect for solo travelers', 'guests': 1, 'booking_params': {'group_adults': 1, 'no_rooms': 1}},
    'double': {'name': 'Double Room', 'description': 'Ideal for couples', 'guests': 2, 'booking_params': {'group_adults': 2, 'no_rooms': 1}},
    'family': {'name': 'Family Room', 'description': 'Great for families', 'guests': 4, 'booking_params': {'group_adults': 2, 'no_rooms': 1, 'group_children': 2}},
    'junior_suite': {'name': 'Junior Suite', 'description': 'Spacious room with sitting area', 'guests': 2, 'booking_params': {'group_adults': 2, 'no_rooms': 1}},
    'suite': {'name': 'Suite/Apartment', 'description': 'Luxury accommodation', 'guests': 3, 'booking_params': {'group_adults': 3, 'no_rooms': 1}}
}

CITIES = {
    'stockholm': {'name': 'Stockholm, Sweden', 'coordinates': [59.3293, 18.0686], 'search_query': 'Stockholm Sweden', 'country': 'se', 'tripadvisor_id': '189852'},
    'paris': {'name': 'Paris, France', 'coordinates': [48.8566, 2.3522], 'search_query': 'Paris France', 'country': 'fr', 'tripadvisor_id': '187147'},
    'london': {'name': 'London, UK', 'coordinates': [51.5074, -0.1278], 'search_query': 'London United Kingdom', 'country': 'gb', 'tripadvisor_id': '186338'},
    'amsterdam': {'name': 'Amsterdam, Netherlands', 'coordinates': [52.3676, 4.9041], 'search_query': 'Amsterdam Netherlands', 'country': 'nl', 'tripadvisor_id': '188590'},
    'barcelona': {'name': 'Barcelona, Spain', 'coordinates': [41.3851, 2.1734], 'search_query': 'Barcelona Spain', 'country': 'es', 'tripadvisor_id': '187497'},
    'rome': {'name': 'Rome, Italy', 'coordinates': [41.9028, 12.4964], 'search_query': 'Rome Italy', 'country': 'it', 'tripadvisor_id': '187791'},
    'berlin': {'name': 'Berlin, Germany', 'coordinates': [52.5200, 13.4050], 'search_query': 'Berlin Germany', 'country': 'de', 'tripadvisor_id': '187323'}
}

# --- External API Functions with Caching ---

@cache
def get_booking_location_id(city_query):
    url = f"https://{BOOKING_API_HOST}/stays/auto-complete"
    try:
        response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params={"query": city_query}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            return data['data'][0].get('id')
    except RequestException as e:
        logging.error(f"Booking.com location ID request failed: {e}")
    return None

@cache
def search_booking_hotels(location_id, checkin, checkout, adults, rooms):
    url = f"https://{BOOKING_API_HOST}/stays/search"
    params = {"locationId": location_id, "checkinDate": checkin, "checkoutDate": checkout, "adults": adults, "rooms": rooms, "currency": "EUR"}
    try:
        response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Booking.com search request failed: {e}")
    return None

@cache
def search_tripadvisor_hotels(geo_id, checkin, checkout, adults):
    url = f"https://{TRIPADVISOR_API_HOST}/api/v1/hotels/searchHotels"
    params = {"geoId": geo_id, "checkIn": checkin, "checkOut": checkout, "adults": adults, "rooms": "1", "currencyCode": "EUR"}
    try:
        response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('data', [])
    except RequestException as e:
        logging.error(f"TripAdvisor search request failed: {e}")
    return []

# --- Data Processing Functions ---

def process_booking_hotels(hotels_data, city_info, search_params):
    processed = []
    hotels_to_process = hotels_data[:20]
    for i, hotel in enumerate(hotels_to_process):
        price = 'N/A'
        price_info = hotel.get('priceBreakdown', {}).get('grossPrice', {}).get('value')
        
        if price_info:
            nights = (datetime.strptime(search_params['checkout'], '%Y-%m-%d') - datetime.strptime(search_params['checkin'], '%Y-%m-%d')).days
            if nights > 0:
                price = int(price_info / nights)
            else:
                price = int(price_info)
        
        rating = hotel.get('reviewScore', 0.0)
        rating = round(float(rating) / 2, 1) if rating > 5 else round(float(rating), 1)

        processed.append({
            'id': hotel.get('id') or f"booking_{i}",
            'name': hotel.get('name', 'Unknown Hotel'),
            'address': hotel.get('address', city_info['name']),
            'coordinates': [float(hotel.get('latitude', city_info['coordinates'][0])), float(hotel.get('longitude', city_info['coordinates'][1]))],
            'price': price,
            'rating': rating or 4.0,
            'source': 'booking.com',
            'room_type': ROOM_TYPES.get(search_params['room_type'], {}).get('name'),
            'booking_url': create_booking_url(hotel, city_info, search_params)
        })
    return processed

def process_tripadvisor_hotels(hotels_data, city_info, search_params):
    processed = []
    hotels_to_process = hotels_data[:15]
    for i, hotel in enumerate(hotels_to_process):
        price = 'N/A'
        price_str = hotel.get('priceForDisplay')
        if price_str:
            numbers = URL_REGEX.findall(price_str.replace(',', ''))
            if numbers:
                price = int(numbers[0])

        processed.append({
            'id': hotel.get('id') or f"tripadvisor_{i}",
            'name': hotel.get('title', 'Unknown Hotel'),
            'address': city_info['name'],
            'coordinates': [float(hotel.get('geoSummary', {}).get('latitude', city_info['coordinates'][0])), float(hotel.get('geoSummary', {}).get('longitude', city_info['coordinates'][1]))],
            'price': price,
            'rating': float(hotel.get('bubbleRating', {}).get('rating', 4.0)),
            'source': 'tripadvisor',
            'room_type': ROOM_TYPES.get(search_params['room_type'], {}).get('name'),
            'booking_url': f"https://www.tripadvisor.com/Search?q={quote_plus(hotel.get('title', 'Hotel'))}"
        })
    return processed

# --- URL & Fallback Generators ---

def create_booking_url(hotel, city_info, params):
    country_code_map = {
        'gb': 'en-gb', 'se': 'sv', 'fr': 'fr', 'es': 'es',
        'it': 'it', 'de': 'de', 'nl': 'nl'
    }
    domain_suffix = country_code_map.get(city_info['country'], city_info['country']) + '.html'
    
    base_params = {
        'ss': hotel.get('name', 'Hotel'),
        'checkin': params['checkin'],
        'checkout': params['checkout'],
        **ROOM_TYPES.get(params['room_type'], {}).get('booking_params', {})
    }
    query_string = urlencode(base_params)
    return f"https://www.booking.com/searchresults.{domain_suffix}?{query_string}"

def get_demo_hotels(city_info, room_type, source):
    logging.warning(f"Using fallback DEMO data for {city_info['name']} from {source}.")
    demo_templates = [
        {'name': f'Grand Hotel {city_info["name"].split(",")[0]}', 'price': 250, 'rating': 4.5},
        {'name': f'Central Plaza {city_info["name"].split(",")[0]}', 'price': 150, 'rating': 4.1},
        {'name': f'Riverside Inn {city_info["name"].split(",")[0]}', 'price': 120, 'rating': 3.9}
    ]
    processed_demos = []
    for i, demo in enumerate(demo_templates):
        processed_demos.append({
            'id': f"demo_{source}_{i}", 'name': demo['name'], 'address': city_info['name'],
            'coordinates': [city_info['coordinates'][0] + (i * 0.01 - 0.01), city_info['coordinates'][1] + (i * 0.01 - 0.01)],
            'price': demo['price'], 'rating': demo['rating'], 'source': source,
            'room_type': ROOM_TYPES.get(room_type, {}).get('name'),
            'booking_url': f"https://www.{source.split('.')[0]}.com/"
        })
    return processed_demos

# --- Unified API Route Handler ---

def handle_hotel_search(source):
    today = datetime.now()
    params = {
        'city': request.args.get('city', 'stockholm').lower(),
        'room_type': request.args.get('room_type', 'double').lower(),
        'checkin': request.args.get('checkin', (today + timedelta(days=1)).strftime('%Y-%m-%d')),
        'checkout': request.args.get('checkout', (today + timedelta(days=2)).strftime('%Y-%m-%d')),
        'adults': request.args.get('adults', '2'),
        'rooms': request.args.get('rooms', '1')
    }
    if params['city'] not in CITIES:
        return jsonify({'error': f"City '{params['city']}' not supported"}), 400
    if params['room_type'] not in ROOM_TYPES:
        return jsonify({'error': f"Room type '{params['room_type']}' not supported"}), 400

    city_info = CITIES[params['city']]
    processed_hotels = []
    data_source = 'live_api'

    try:
        api_data = None
        if source == 'booking':
            location_id = get_booking_location_id(city_info['search_query'])
            if location_id:
                api_data = search_booking_hotels(location_id, params['checkin'], params['checkout'], params['adults'], params['rooms'])
                if api_data:
                    processed_hotels = process_booking_hotels(api_data.get('data', []), city_info, params)
        
        elif source == 'tripadvisor':
            geo_id = city_info.get('tripadvisor_id')
            if geo_id:
                api_data = search_tripadvisor_hotels(geo_id, params['checkin'], params['checkout'], params['adults'])
                if api_data:
                    processed_hotels = process_tripadvisor_hotels(api_data, city_info, params)

        if not processed_hotels:
            data_source = 'demo_fallback'
            processed_hotels = get_demo_hotels(city_info, params['room_type'], source)

        return jsonify({
            'city': city_info['name'],
            'hotels': processed_hotels,
            'total_found': len(processed_hotels),
            'search_params': params,
            'source': source,
            'data_source': data_source
        })

    except Exception as e:
        logging.critical(f"Unhandled exception in handle_hotel_search for source '{source}': {e}", exc_info=True)
        return jsonify({'error': 'An unexpected internal server error occurred.'}), 500

# --- Flask Routes ---

@app.route('/')
def home():
    return render_template_string('<h1>STAYFINDR Backend v5.4</h1><p>Production-ready. All systems operational.</p>')

@app.route('/api/cities')
def get_cities_route():
    return jsonify({'cities': CITIES, 'total': len(CITIES)})

@app.route('/api/room-types')
def get_room_types_route():
    return jsonify({'room_types': ROOM_TYPES, 'total': len(ROOM_TYPES)})

@app.route('/api/hotels/booking')
def get_booking_hotels_route():
    return handle_hotel_search(source='booking')

@app.route('/api/hotels/tripadvisor')
def get_tripadvisor_hotels_route():
    return handle_hotel_search(source='tripadvisor')

@app.route('/api/hotels')
def get_hotels_legacy_route():
    return handle_hotel_search(source='booking')

@app.route('/test')
def test_endpoint_route():
    return jsonify({'status': 'STAYFINDR Backend v5.4 Active', 'caching': 'enabled', 'logging': 'enabled'})

# --- Application Startup ---

if __name__ == '__main__':
    logging.info("🚀 Starting STAYFINDR Backend v5.4...")
    logging.info("▶️ Features: Unified Logic, Caching, Logging, Dual-Source, Secure, Robust Lines.")
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not is_production, host='0.0.0.0', port=port)
