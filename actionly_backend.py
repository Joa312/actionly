# STAYFINDR BACKEND v6.0 - Production Ready with CSV Data Loading
# Reads city data from an external cities.csv file for easy management.

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus
from functools import cache
import re
import csv # REVISION: Imported the CSV module

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

# REVISION: Function to load cities from the CSV file
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

# REVISION: The CITIES dictionary is now loaded from the CSV file at startup.
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
        logging.error(f"Booking.com search request failed: {
