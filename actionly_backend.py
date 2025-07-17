# STAYFINDR BACKEND v6.7 - Robust Error Handling & Cache Removal
# FIX: Removed @cache from API calls to ensure fresh data and prevent caching of failed requests.
# FIX: Rewrote search handler to provide clear error messages instead of silently falling back to demo data.
# FIX: This version correctly distinguishes between a failed API call and a successful call that returns zero results.

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus
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

CORS(app, origins=[
    "https://joa312.github.io",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:5000"
])

# --- API & Data Constants ---
BOOKING_API_HOST = "booking-com18.p.rapidapi.com"
TRIPADVISOR_API_HOST = "tripadvisor16.p.rapidapi.com"

BOOKING_HOTEL_LIMIT = 20
TRIPADVISOR_HOTEL_LIMIT = 15

URL_REGEX = re.compile(r'\d+')

ROOM_TYPES = {
    'single': {'name': 'Single Room', 'description': 'Perfect for solo travelers', 'guests': 1, 'booking_params': {'group_adults': 1, 'no_rooms': 1}},
    'double': {'name': 'Double Room', 'description': 'Ideal for couples', 'guests': 2, 'booking_params': {'group_adults': 2, 'no_rooms': 1}},
    'family': {'name': 'Family Room', 'description': 'Great for families', 'guests': 4, 'booking_params': {'group_adults': 2, 'no_rooms': 1, 'group_children': 2}},
    'junior_suite': {'name': 'Junior Suite', 'description': 'Spacious room with sitting area', 'guests': 2, 'booking_params': {'group_adults': 2, 'no_rooms': 1}},
    'suite': {'name': 'Suite/Apartment', 'description': 'Luxury accommodation', 'guests': 3, 'booking_params': {'group_adults': 3, 'no_rooms': 1}}
}

# Function to load cities from the CSV file
def load_cities_from_csv(filename='cities.csv'):
    cities = {}
    try:
        with open(filename, mode='r', encoding='utf-8-sig') as infile:
            try:
                dialect = csv.Sniffer().sniff(infile.read(1024))
                infile.seek(0) 
                reader = csv.DictReader(infile, dialect=dialect)
            except csv.Error:
                logging.warning("CSV Sniffer failed, falling back to comma delimiter.")
                infile.seek(0)
                reader = csv.DictReader(infile)

            for i, row in enumerate(reader):
                if not any(row.values()): continue
                key = row.get('key')
                if not key:
                    logging.warning(f"Skipping row {i+2} in {filename} due to missing key.")
                    continue
                lat, lon = 0.0, 0.0
                try:
                    lat = float(row.get('lat', '0').replace(',', '.'))
                    lon = float(row.get('lon', '0').replace(',', '.'))
                except (ValueError, TypeError):
                    logging.warning(f"Could not parse coordinates for city '{key}' on row {i+2}.")
                
                cities[key] = {
                    'name': row.get('name', 'N/A').replace('"', '').strip(),
                    'coordinates': [lat, lon],
                    'country': row.get('country', ''),
                }
        logging.info(f"Successfully loaded {len(cities)} cities from {filename}.")
        return cities
    except FileNotFoundError:
        logging.error(f"CRITICAL: The file {filename} was not found.")
        raise
    except Exception as e:
        logging.error(f"CRITICAL: Failed to read or parse {filename}. Error: {e}", exc_info=True)
        raise

CITIES = load_cities_from_csv('cities.csv')

# --- External API Functions ---
# FIX: Removed @cache decorator to prevent caching failed requests.

def search_booking_hotels_by_coords(latitude, longitude, checkin, checkout, adults, rooms):
    url = f"https://{BOOKING_API_HOST}/stays/search-by-coordinates"
    params = {
        "latitude": latitude, "longitude": longitude, "checkinDate": checkin,
        "checkoutDate": checkout, "adults": adults, "rooms": rooms, "currency": "EUR"
    }
    # The try/except block is now in the main handler for better error propagation.
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params=params, timeout=15)
    response.raise_for_status()  # Will raise an exception for non-2xx responses
    return response.json()

def search_tripadvisor_hotels_by_coords(latitude, longitude, checkin, checkout, adults):
    url = f"https://{TRIPADVISOR_API_HOST}/api/v1/hotels/searchHotelsByCoordinates"
    params = {
        "latitude": latitude, "longitude": longitude, "checkIn": checkin,
        "checkOut": checkout, "adults": adults, "rooms": "1", "currencyCode": "EUR"
    }
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get('data', {}).get('data', [])

# --- Data Processing Functions ---

def process_booking_hotels(hotels_data, city_info, search_params):
    processed = []
    for i, hotel in enumerate(hotels_data[:BOOKING_HOTEL_LIMIT]):
        price = 'N/A'
        if price_info := hotel.get('priceBreakdown', {}).get('grossPrice', {}).get('value'):
            nights = (datetime.strptime(search_params['checkout'], '%Y-%m-%d') - datetime.strptime(search_params['checkin'], '%Y-%m-%d')).days
            price = int(price_info / nights) if nights > 0 else int(price_info)
        
        rating = hotel.get('reviewScore', 0.0)
        processed.append({
            'id': hotel.get('id') or f"booking_{i}", 'name': hotel.get('name', 'Unknown Hotel'),
            'address': hotel.get('address', city_info['name']), 'phone': hotel.get('phone', None),
            'coordinates': [float(hotel.get('latitude', 0)), float(hotel.get('longitude', 0))],
            'price': price, 'rating': round(float(rating) / 2, 1) if rating > 5 else round(float(rating), 1),
            'source': 'booking.com', 'room_type': ROOM_TYPES.get(search_params['room_type'], {}).get('name'),
            'booking_url': create_booking_url(hotel, city_info, search_params)
        })
    return processed

def process_tripadvisor_hotels(hotels_data, city_info, search_params):
    processed = []
    for i, hotel in enumerate(hotels_data[:TRIPADVISOR_HOTEL_LIMIT]):
        price = 'N/A'
        if price_str := hotel.get('priceForDisplay'):
            if numbers := URL_REGEX.findall(price_str.replace(',', '')):
                price = int(numbers[0])
        processed.append({
            'id': hotel.get('id') or f"tripadvisor_{i}", 'name': hotel.get('title', 'Unknown Hotel'),
            'address': city_info['name'], 'phone': hotel.get('phone', None),
            'coordinates': [float(hotel.get('geoSummary', {}).get('latitude', 0)), float(hotel.get('geoSummary', {}).get('longitude', 0))],
            'price': price, 'rating': float(hotel.get('bubbleRating', {}).get('rating', 4.0)),
            'source': 'tripadvisor', 'room_type': ROOM_TYPES.get(search_params['room_type'], {}).get('name'),
            'booking_url': f"https://www.tripadvisor.com/Search?q={quote_plus(hotel.get('title', 'Hotel'))}"
        })
    return processed

# --- URL & Fallback Generators ---

def create_booking_url(hotel, city_info, params):
    country_code_map = {'gb': 'en-gb', 'se': 'sv', 'fr': 'fr', 'es': 'es', 'it': 'it', 'de': 'de', 'nl': 'nl'}
    domain_suffix = country_code_map.get(city_info['country'], city_info['country']) + '.html'
    base_params = {'ss': hotel.get('name', 'Hotel'), 'checkin': params['checkin'], 'checkout': params['checkout'], **ROOM_TYPES.get(params['room_type'], {}).get('booking_params', {})}
    return f"https://www.booking.com/searchresults.{domain_suffix}?{urlencode(base_params)}"

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
    lat, lon = city_info['coordinates']
    processed_hotels = []
    data_source = 'live_api'

    try:
        logging.info(f"Attempting to fetch hotels from '{source}' for '{city_info['name']}'.")
        if source == 'booking':
            api_data = search_booking_hotels_by_coords(lat, lon, params['checkin'], params['checkout'], params['adults'], params['rooms'])
            processed_hotels = process_booking_hotels(api_data.get('data', []), city_info, params)
        elif source == 'tripadvisor':
            api_data = search_tripadvisor_hotels_by_coords(lat, lon, params['checkin'], params['checkout'], params['adults'])
            processed_hotels = process_tripadvisor_hotels(api_data, city_info, params)
        else:
            return jsonify({'error': f"Source '{source}' is not supported."}), 400
        
        if not processed_hotels:
            logging.warning(f"Live API call to '{source}' was successful but returned 0 hotels.")
            data_source = 'live_api_empty'

    except RequestException as e:
        # FIX: Catch API errors explicitly and return a clear error message to the frontend.
        logging.error(f"API call to '{source}' failed: {e}")
        error_message = f"Kunde inte hämta data från {source.capitalize()}. Tjänsten kan vara nere, eller så kan din API-nyckel ha gått ut."
        return jsonify({'error': error_message}), 503 # 503 Service Unavailable is appropriate here
    except Exception as e:
        logging.critical(f"An unhandled exception occurred for source '{source}': {e}", exc_info=True)
        return jsonify({'error': 'Ett oväntat internt fel uppstod.'}), 500

    return jsonify({
        'city': city_info['name'],
        'hotels': processed_hotels,
        'total_found': len(processed_hotels),
        'search_params': params,
        'source': source,
        'data_source': data_source
    })

# --- Flask Routes ---
@app.route('/')
def home():
    return render_template_string('<h1>STAYFINDR Backend v6.7</h1><p>Robust error handling implemented. No more silent fallbacks.</p>')

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

@app.route('/test')
def test_endpoint_route():
    return jsonify({'status': 'STAYFINDR Backend v6.7 Active'})

# --- Application Startup ---
if __name__ == '__main__':
    logging.info("🚀 Starting STAYFINDR Backend v6.7...")
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not is_production, host='0.0.0.0', port=port)
