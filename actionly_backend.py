# STAYFINDR BACKEND - European Hotel Search Engine
# Flask backend with RapidAPI Booking.com integration + WORKING Hotels.com
# BREAKTHROUGH: Two-step Hotels.com using suggest + Hotels/Search

import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import time
from datetime import datetime
from urllib.parse import quote_plus
import re

app = Flask(__name__)
CORS(app)

# RapidAPI Configuration
RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
RAPIDAPI_HOST_BOOKING = "booking-com18.p.rapidapi.com"
RAPIDAPI_HOST_HOTELS = "hotels4.p.rapidapi.com"

# European Cities Configuration - 29 major destinations
CITIES = {
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
    },
    'amsterdam': {
        'name': 'Amsterdam, Netherlands',
        'coordinates': [52.3676, 4.9041],
        'search_query': 'Amsterdam Netherlands'
    },
    'barcelona': {
        'name': 'Barcelona, Spain',
        'coordinates': [41.3851, 2.1734],
        'search_query': 'Barcelona Spain'
    }
}

# Room Type Configuration with Junior Suite
ROOM_TYPES = {
    'single': {
        'name': 'Single Room',
        'description': 'Perfect for solo travelers',
        'guests': 1,
        'keywords': ['single', 'solo', 'individual']
    },
    'double': {
        'name': 'Double Room',
        'description': 'Ideal for couples',
        'guests': 2,
        'keywords': ['double', 'couple', 'standard', 'queen', 'king']
    },
    'family': {
        'name': 'Family Room',
        'description': 'Spacious accommodation for families',
        'guests': 4,
        'keywords': ['family', 'triple', 'quad', 'bunk', 'connecting']
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'description': 'Spacious room with sitting area',
        'guests': 2,
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded', 'deluxe']
    },
    'suite': {
        'name': 'Suite/Apartment',
        'description': 'Luxury accommodation with separate living area',
        'guests': 3,
        'keywords': ['suite', 'apartment', 'penthouse', 'presidential', 'luxury', 'executive']
    }
}

def search_hotels_com_api_working(city, checkin, checkout, adults):
    """Search hotels using WORKING two-step process: suggest + Hotels/Search"""
    
    # Step 1: Get destinationId using /suggest (YOUR WORKING ENDPOINT)
    suggest_url = "https://hotels4.p.rapidapi.com/suggest"
    
    suggest_params = {
        "query": city,
        "locale": "en_US"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_HOTELS
    }
    
    try:
        # Step 1: Get destination ID
        suggest_response = requests.get(suggest_url, headers=headers, params=suggest_params)
        print(f"Hotels
