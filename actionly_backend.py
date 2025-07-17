# STAYFINDR BACKEND v7.9 - Fully Dynamic Search
# FINAL FIX: Re-implemented dynamic Geo ID lookup for TripAdvisor.
# The system now dynamically fetches location IDs for BOTH Booking.com and TripAdvisor before every search.
# This removes all reliance on static, potentially outdated IDs from the CSV file, which was the root cause of the empty results.

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus
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
TRIPADVISOR_API_HOST = "tripadvisor-com1.p.rapidapi.com"
BOOKING_HOTEL_LIMIT = 20
TRIPADVISOR_HOTEL_LIMIT = 15
URL_REGEX = re.compile(r'\d+')

# --- Data Loading ---
def load_cities_from_csv(filename='cities.csv'):
    """Loads cities from CSV. Only 'key', 'name', and 'search_query' are now used."""
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

def get_booking_location_id(city_query):
    """Fetches location ID from the booking-com18 endpoint."""
    if not city_query: return None
    url = f"https://{BOOKING_API_HOST}/stays/auto-complete"
    params = {"query": city_query}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get('data'):
        return data['data'][0].get('id')
    logging.warning(f"Could not find Booking.com location ID for query: {city_query}")
    return None

def search_booking_hotels(location_id, checkin, checkout, adults, rooms):
    """Searches Booking.com hotels using a location ID."""
    url = f"https://{BOOKING_API_HOST}/stays/search"
    params = {"locationId": location_id, "checkinDate": checkin, "checkoutDate": checkout, "adults": adults, "rooms": rooms, "currency": "EUR"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": BOOKING_API_HOST}, params=params, timeout=15)
    response.raise_for_status()
    return response.json()

def get_tripadvisor_geo_id(city_name):
    """Dynamically fetches the Geo ID from TripAdvisor based on city name."""
    url = f"https://{TRIPADVISOR_API_HOST}/locations/search"
    params = {"query": city_name, "lang": "en_US", "units": "km"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get('data'):
        for item in data['data']:
            if item.get('result_type') == 'geography':
                if geo_id := item.get('result_object', {}).get('location_id'):
                    logging.info(f"Found TripAdvisor geoId: {geo_id} for city: {city_name}")
                    return geo_id
    logging.warning(f"Could not find TripAdvisor geoId for city: {city_name}")
    return None

def search_tripadvisor_hotels(geo_id, checkin, checkout, adults):
    """Searches TripAdvisor hotels using a Geo ID."""
    if not geo_id: return None
    url = f"https://{TRIPADVISOR_API_HOST}/hotels/search"
    params = {"geoId": geo_id, "checkIn": checkin, "checkOut": checkout, "adults": adults, "rooms": "1", "currencyCode": "EUR"}
    response = requests.get(url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": TRIPADVISOR_API_HOST}, params=params, timeout=15)
    response.raise_for_status()
    return response.json()

# --- Data Processing Functions ---

def process_booking_hotels(api_data, search_params):
    processed = []
    hotels_data = api_data.get('data', [])
    if not isinstance(hotels_data, list):
        logging.warning(f"Booking.com data processing received non-list data: {type(hotels_data)}")
        return []

    for i, hotel in enumerate(hotels_data[:BOOKING_HOTEL_LIMIT]):
        price = 'N/A'
        if price_info := hotel.get('priceBreakdown', {}).get('grossPrice', {}).get('value'):
            nights = (datetime.strptime(search_params['checkout'], '%Y-%m-%d') - datetime.strptime(search_params['checkin'], '%Y-%m-%d')).days
            price = int(price_info / nights) if nights > 0 else int(price_info)
        processed.append({
            'id': hotel.get('id') or f"booking_{i}", 'name': hotel.get('name', 'Unknown Hotel'),
            'address': hotel.get('address', 'N/A'),
            'coordinates': [float(hotel.get('latitude', 0)), float(hotel.get('longitude', 0))],
            'price': price, 'rating': round(float(hotel.get('reviewScore', 0.0)) / 2, 1),
            'source': 'booking.com', 'booking_url': hotel.get('url', '#')
        })
    return processed

def process_tripadvisor_hotels(api_data):
    processed = []
    hotels_data = api_data.get('data', [])
    if not isinstance(hotels_data, list):
        logging.warning(f"TripAdvisor API did not return a list of hotels.")
        return []

    for i, hotel in enumerate(hotels_data[:TRIPADVISOR_HOTEL_LIMIT]):
        price = 'N/A'
        if price_str := hotel.get('priceForDisplay'):
            if numbers := URL_REGEX.findall(price_str.replace(',', '')):
                price = int(numbers[0])
        processed.append({
            'id': hotel.get('id') or f"tripadvisor_{i}", 'name': hotel.get('title', 'Unknown Hotel'),
            'address': hotel.get('secondaryInfo', 'N/A'),
            'coordinates': [float(hotel.get('geoSummary', {}).get('latitude', 0)), float(hotel.get('geoSummary', {}).get('longitude', 0))],
            'price': price, 'rating': float(hotel.get('bubbleRating', {}).get('rating', 4.0)),
            'source': 'tripadvisor',
            'booking_url': f"https://www.tripadvisor.com{hotel.get('commerceUrl')}" if hotel.get('commerceUrl') else f"https://www.tripadvisor.com/Search?q={quote_plus(hotel.get('title', 'Hotel'))}"
        })
    return processed

# --- Unified API Route Handler ---

def handle_hotel_search(source):
    today = datetime.now()
    params = {'city_key': request.args.get('city', 'stockholm').lower(), 'checkin': request.args.get('checkin', (today + timedelta(days=1)).strftime('%Y-%m-%d')), 'checkout': request.args.get('checkout', (today + timedelta(days=2)).strftime('%Y-%m-%d')), 'adults': request.args.get('adults', '2'), 'rooms': request.args.get('rooms', '1')}
    if params['city_key'] not in CITIES: return jsonify({'error': f"City '{params['city_key']}' not supported"}), 400
    
    city_info = CITIES[params['city_key']]
    city_name = city_info['name']
    
    try:
        logging.info(f"Handling '{source}' search for '{city_name}'.")
        if source == 'booking':
            location_id = get_booking_location_id(city_info['search_query'])
            if location_id:
                api_data = search_booking_hotels(location_id, params['checkin'], params['checkout'], params['adults'], params['rooms'])
                processed_hotels = process_booking_hotels(api_data, params)
            else:
                return jsonify({'error': f"Kunde inte hitta ett giltigt ID för '{city_name}' på Booking.com."}), 404

        elif source == 'tripadvisor':
            geo_id = get_tripadvisor_geo_id(city_name)
            if geo_id:
                api_data = search_tripadvisor_hotels(geo_id, params['checkin'], params['checkout'], params['adults'])
                processed_hotels = process_tripadvisor_hotels(api_data)
            else:
                return jsonify({'error': f"Kunde inte hitta ett giltigt ID för '{city_name}' på TripAdvisor."}), 404
        else:
            return jsonify({'error': f"Source '{source}' is not supported."}), 400
        
    except RequestException as e:
        status_code = e.response.status_code if e.response is not None else 500
        logging.error(f"API call to '{source}' failed with status {status_code}: {e}")
        return jsonify({'error': f"Kunde inte hämta data från {source.capitalize()}. Felkod: {status_code}. Kontrollera din prenumeration på RapidAPI."}), 503
    except Exception as e:
        logging.critical(f"An unhandled exception occurred for source '{source}': {e}", exc_info=True)
        return jsonify({'error': 'Ett oväntat internt fel uppstod.'}), 500

    return jsonify({'city': city_name, 'hotels': processed_hotels, 'total_found': len(processed_hotels), 'search_params': params})

# --- Flask Routes ---
@app.route('/')
def home(): return render_template_string('<h1>STAYFINDR Backend v7.9</h1><p>Fully dynamic search for all services.</p>')

@app.route('/api/cities')
def get_cities_route(): return jsonify({'cities': CITIES})

@app.route('/api/room-types')
def get_room_types_route():
    # Simplified room types as they are mainly for display
    room_types = {
        'single': {'name': 'Single Room', 'guests': 1},
        'double': {'name': 'Double Room', 'guests': 2},
        'family': {'name': 'Family Room', 'guests': 4}
    }
    return jsonify({'room_types': room_types})

@app.route('/api/hotels/booking')
def get_booking_hotels_route(): return handle_hotel_search(source='booking')

@app.route('/api/hotels/tripadvisor')
def get_tripadvisor_hotels_route(): return handle_hotel_search(source='tripadvisor')

@app.route('/test')
def test_endpoint_route(): return jsonify({'status': 'STAYFINDR Backend v7.9 Active'})

# --- Application Startup ---
if __name__ == '__main__':
    logging.info("🚀 Starting STAYFINDR Backend v7.9...")
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not is_production, host='0.0.0.0', port=port)
