# STAYFINDR BACKEND v6.0 - Production Ready with CSV Data Loading
# Reads city data from an external cities.csv file for easy management.

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus
from functools import cache
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
    """
    Loads city data from a CSV file and formats it into the required dictionary structure.
    """
    cities = {}
    try:
        # Use utf-8-sig to handle potential BOM (Byte Order Mark) from Excel
        with open(filename, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                key = row['key']
                cities[key] = {
                    'name': row['name'],
                    'coordinates': [float(row['lat']), float(row['lon'])],
                    'search_query': row['search_query'],
                    'country': row['country'],
                    'tripadvisor_id': row['tripadvisor_id']
                }
        logging.info(f"Successfully loaded {len(cities)} cities from {filename}.")
        return cities
    except FileNotFoundError:
        logging.error(f"CRITICAL: The file {filename} was not found. The application cannot start without it.")
        raise
    except Exception as e:
        logging.error(f"CRITICAL: Failed to read or parse {filename}. Error: {e}")
        raise

# The CITIES dictionary is now loaded from the CSV file at startup.
CITIES = load_cities_from_csv('cities.csv')

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
    hotels_to_process = hotels_data[:BOOKING_HOTEL_LIMIT]
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
    hotels_to_process = hotels_data[:TRIPADVISOR_HOTEL_LIMIT]
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
            'coordinates': [city_info['coordinates'][0] + (i * 0.01 - 0.01), city_info['coordinates'][1] + (i * 0
