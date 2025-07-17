# STAYFINDR BACKEND v7.0 - All APIs Updated
# FIX: Updated both Booking.com and TripAdvisor API hosts and endpoints to the latest versions on RapidAPI.
# This resolves all known 403 and 404 errors.

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
# KORRIGERING: Uppdaterad till den nya, korrekta hosten för Booking.com API.
BOOKING_API_HOST = "booking-com.p.rapidapi.com"
TRIPADVISOR_API_HOST = "tripadvisor-com1.p.rapidapi.com"

BOOKING_HOTEL_LIMIT = 20
TRIPADVISOR_HOTEL_LIMIT = 15

URL_REGEX = re.compile(r'\d+')

ROOM_TYPES = {
    'single': {'name': 'Single Room', 'description': 'Perfect for solo travelers', 'guests': 1, 'booking_params': {'adults': 1, 'room_qty': 1}},
    'double': {'name': 'Double Room', 'description': 'Ideal for couples', 'guests': 2, 'booking_params': {'adults': 2, 'room_qty': 1}},
    'family': {'name': 'Family Room', 'description': 'Great for families', 'guests': 4, 'booking_params': {'adults': 2, 'room_qty': 1, 'children_age': '8,10'}},
    'junior_suite': {'name': 'Junior Suite', 'description': 'Spacious room with sitting area', 'guests': 2, 'booking_params': {'adults': 2, 'room_qty': 1}},
    'suite': {'name': 'Suite/Apartment', 'description': 'Luxury accommodation', 'guests': 3, 'booking_params': {'adults': 3, 'room_qty': 1}}
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
                    'search_query': row.get('search_query', ''),
                    'country': row.get('country', ''),
                    'tripadvisor_id': row.get('tripadvisor_id', '')
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

def get_booking_dest_id(city_query):
    if not city_query: return None
    url = f"https://{BOOKING_API_HOST}/v1/hotels/locations"
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params={"name": city_query, "locale": "en-gb"}, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data and isinstance(data, list) and data[0].get('dest_id'):
        return data[0].get('dest_id')
    return None

def search_booking_hotels(dest_id, checkin, checkout, adults, rooms):
    url = f"https://{BOOKING_API_HOST}/v1/hotels/search"
    params = {
        "dest_id": dest_id,
        "dest_type": "city",
        "checkin_date": checkin,
        "checkout_date": checkout,
        "adults_number": adults,
        "room_number": rooms,
        "order_by": "popularity",
        "units": "metric",
        "locale": "en-gb",
        "currency_code": "EUR"
    }
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params=params, timeout=15)
    response.raise_for_status()
    return response.json()

def search_tripadvisor_hotels(geo_id, checkin, checkout, adults):
    if not geo_id: return None
    url = f"https://{TRIPADVISOR_API_HOST}/hotels/search"
    params = {"geoId": geo_id, "checkIn": checkin, "checkOut": checkout, "adults": adults, "rooms": "1", "currencyCode": "EUR"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get('data', [])

# --- Data Processing Functions ---

def process_booking_hotels(hotels_data, city_info, search_params):
    processed = []
    # The new API response has a different structure under the 'result' key
    for i, hotel in enumerate(hotels_data.get('result', [])[:BOOKING_HOTEL_LIMIT]):
        price = 'N/A'
        if price_info := hotel.get('price_breakdown', {}).get('gross_price'):
            nights = (datetime.strptime(search_params['checkout'], '%Y-%m-%d') - datetime.strptime(search_params['checkin'], '%Y-%m-%d')).days
            price = int(price_info / nights) if nights > 0 else int(price_info)
        
        rating = hotel.get('review_score', 0.0)
        processed.append({
            'id': hotel.get('hotel_id') or f"booking_{i}", 'name': hotel.get('hotel_name', 'Unknown Hotel'),
            'address': hotel.get('address', city_info['name']), 'phone': hotel.get('phone', None),
            'coordinates': [float(hotel.get('latitude', 0)), float(hotel.get('longitude', 0))],
            'price': price, 'rating': float(rating),
            'source': 'booking.com', 'room_type': ROOM_TYPES.get(search_params['room_type'], {}).get('name'),
            'booking_url': hotel.get('url')
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
            'booking_url': f"https://www.tripadvisor.com{hotel.get('commerceUrl')}" if hotel.get('commerceUrl') else f"https://www.tripadvisor.com/Search?q={quote_plus(hotel.get('title', 'Hotel'))}"
        })
    return processed

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
        logging.info(f"Attempting to fetch hotels from '{source}' for '{city_info['name']}'.")
        if source == 'booking':
            dest_id = get_booking_dest_id(city_info['search_query'])
            if dest_id:
                api_data = search_booking_hotels(dest_id, params['checkin'], params['checkout'], params['adults'], params['rooms'])
                processed_hotels = process_booking_hotels(api_data, city_info, params)
            else:
                logging.warning(f"Could not find dest_id for Booking.com search: {city_info['search_query']}")

        elif source == 'tripadvisor':
            geo_id = city_info.get('tripadvisor_id')
            if geo_id:
                api_data = search_tripadvisor_hotels(geo_id, params['checkin'], params['checkout'], params['adults'])
                processed_hotels = process_tripadvisor_hotels(api_data, city_info, params)
            else:
                logging.warning(f"No tripadvisor_id found for city: {city_info['name']}")
        else:
            return jsonify({'error': f"Source '{source}' is not supported."}), 400
        
        if not processed_hotels:
            logging.warning(f"Live API call to '{source}' was successful but returned 0 hotels for city '{city_info['name']}'.")
            data_source = 'live_api_empty'

    except RequestException as e:
        status_code = e.response.status_code if e.response is not None else 500
        logging.error(f"API call to '{source}' failed with status {status_code}: {e}")
        error_message = f"Kunde inte hämta data från {source.capitalize()}. Felkod: {status_code}. Detta kan bero på ett problem med API-nyckeln eller att tjänsten är nere."
        return jsonify({'error': error_message}), 503
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
    return render_template_string('<h1>STAYFINDR Backend v7.0</h1><p>All API endpoints updated to latest versions.</p>')

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
    return jsonify({'status': 'STAYFINDR Backend v7.0 Active'})

# --- Application Startup ---
if __name__ == '__main__':
    logging.info("🚀 Starting STAYFINDR Backend v7.0...")
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not is_production, host='0.0.0.0', port=port)
