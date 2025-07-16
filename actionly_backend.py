# STAYFINDR BACKEND v5.3 - Final Foolproof Version
# Contains permanent fixes for all copy-paste related SyntaxErrors.
# Long lines have been refactored for maximum robustness.

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode
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
    for i, hotel in enumerate
