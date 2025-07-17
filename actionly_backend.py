#!/usr/bin/env python3
"""
STAYFINDR Backend API - Flask Version
European Hotel Search Engine med BÅDE Booking.com OCH TripAdvisor
Version: 2.0 - Flask Dual Platform Edition
"""

import csv
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus

import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Logging konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app initiering
app = Flask(__name__)
CORS(app)

# API konfiguration
BOOKING_HOST = "booking-com15.p.rapidapi.com"
TRIPADVISOR_HOST = "tripadvisor1.p.rapidapi.com"
API_KEY = os.getenv("RAPIDAPI_KEY", "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999")

BOOKING_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": BOOKING_HOST
}

TRIPADVISOR_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": TRIPADVISOR_HOST
}

# Room type mappings
ROOM_TYPE_MAPPING = {
    "single": {"guests": 1, "description": "Single Room - Perfect for solo travelers"},
    "double": {"guests": 2, "description": "Double Room - Ideal for couples"},
    "family": {"guests": 4, "description": "Family Room - Spacious for families"},
    "junior_suite": {"guests": 2, "description": "Junior Suite - Spacious room with sitting area"},
    "suite": {"guests": 3, "description": "Suite/Apartment - Premium accommodation"}
}

# Country codes för lokaliserade booking URLs
COUNTRY_CODES = {
    'stockholm': 'sv', 'oslo': 'no', 'helsinki': 'fi', 'copenhagen': 'dk',
    'paris': 'fr', 'lyon': 'fr', 'nice': 'fr',
    'london': 'en-gb', 'edinburgh': 'en-gb',
    'amsterdam': 'nl', 'brussels': 'nl',
    'barcelona': 'es', 'madrid': 'es', 'palma': 'es', 'ibiza': 'es',
    'rome': 'it', 'milano': 'it', 'florence': 'it',
    'berlin': 'de', 'munich': 'de',
    'vienna': 'de', 'zurich': 'de',
    'prague': 'cs', 'warsaw': 'pl', 'budapest': 'hu',
    'dublin': 'en-gb', 'lisbon': 'pt', 'athens': 'el', 'santorini': 'el'
}

# TripAdvisor location mappings
TRIPADVISOR_LOCATIONS = {
    'stockholm': '189839',
    'paris': '187147', 
    'london': '186338',
    'barcelona': '187497',
    'rome': '187791',
    'amsterdam': '188590',
    'berlin': '187323',
    'copenhagen': '189541',
    'vienna': '190454',
    'prague': '274707',
    'madrid': '187514',
    'milan': '187849',
    'zurich': '188113',
    'oslo': '190479',
    'helsinki': '189896',
    'warsaw': '274856',
    'budapest': '274887',
    'dublin': '186605',
    'lisbon': '189158',
    'athens': '189398'
}

# Helper functions
def validate_api_key():
    """Validera API-nyckel"""
    if not API_KEY or API_KEY == "YOUR_RAPIDAPI_KEY":
        logger.error("API key not configured")
        return False
    return True

def get_city_id(city_name: str) -> Optional[str]:
    """Hämta city ID från CSV-fil för Booking.com"""
    csv_file = "cities.csv"
    
    if not os.path.exists(csv_file):
        logger.warning(f"Cities CSV file not found: {csv_file}")
        # Fallback mapping för vanliga städer
        fallback_cities = {
            'stockholm': '1371',
            'paris': '-1456928',
            'london': '-2601889',
            'barcelona': '-372490',
            'rome': '-126693',
            'amsterdam': '-2140479',
            'berlin': '-1746443',
            'copenhagen': '-2745240',
            'vienna': '-1995499',
            'prague': '-553173'
        }
        return fallback_cities.get(city_name.lower())
    
    try:
        with open(csv_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["city"].strip().lower() == city_name.strip().lower():
                    logger.info(f"Found Booking.com city ID for {city_name}: {row['dest_id']}")
                    return row["dest_id"]
    except Exception as e:
        logger.error(f"Error reading cities.csv: {e}")
        return None
    
    logger.warning(f"City not found in CSV: {city_name}")
    return None

def search_hotels_booking_api(dest_id: str, checkin: str, checkout: str, 
                             adults: int, rooms: int) -> Optional[Dict]:
    """Sök hotell via Booking.com API"""
    url = f"https://{BOOKING_HOST}/api/v1/hotels/searchHotels"
    
    params = {
        "dest_id": dest_id,
        "dest_type": "city",
        "checkin_date": checkin,
        "checkout_date": checkout,
        "room_number": rooms,
        "guest_number": adults,
        "locale": "en-gb",
        "currency": "EUR",
        "order_by": "popularity",
        "units": "metric",
        "filter_by_currency": "EUR"
    }
    
    try:
        response = requests.get(url, headers=BOOKING_HEADERS, params=params, timeout=30)
        logger.info(f"Booking.com API call: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Booking.com API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error calling Booking.com API: {e}")
        return None

def get_tripadvisor_hotels(location_id: str, limit: int = 30) -> Optional[Dict]:
    """Hämta hotell från TripAdvisor API"""
    url = f"https://{TRIPADVISOR_HOST}/hotels/list"
    
    params = {
        "location_id": location_id,
        "limit": str(limit),
        "sort": "recommended",
        "offset": "0",
        "currency": "EUR",
        "lang": "en_US"
    }
    
    try:
        response = requests.get(url, headers=TRIPADVISOR_HEADERS, params=params, timeout=30)
        logger.info(f"TripAdvisor API call: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"TripAdvisor API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error calling TripAdvisor API: {e}")
        return None

def find_tripadvisor_hotel_by_name(hotel_name: str, tripadvisor_hotels: List[Dict]) -> Optional[Dict]:
    """Matcha Booking.com hotell med TripAdvisor hotell baserat på namn"""
    if not tripadvisor_hotels:
        return None
    
    # Normalisera hotellnamn för matchning
    normalized_booking_name = hotel_name.lower().strip()
    
    # Exakt matchning först
    for ta_hotel in tripadvisor_hotels:
        ta_name = ta_hotel.get('name', '').lower().strip()
        if normalized_booking_name == ta_name:
            return ta_hotel
    
    # Partiell matchning som backup
    for ta_hotel in tripadvisor_hotels:
        ta_name = ta_hotel.get('name', '').lower().strip()
        # Kontrollera om hotellnamnen överlappar med minst 2 ord
        booking_words = set(normalized_booking_name.split())
        ta_words = set(ta_name.split())
        
        if len(booking_words.intersection(ta_words)) >= 2:
            return ta_hotel
    
    return None

def create_booking_url(hotel: Dict, city_key: str, checkin: str, checkout: str, 
                      adults: int, rooms: int, room_type: Optional[str] = None) -> str:
    """Skapa lokaliserad Booking.com URL med hotellnamn"""
    hotel_name = hotel.get('name', 'Hotel')
    hotel_id = hotel.get('id') or hotel.get('hotel_id')
    
    # Hämta landskod för staden
    country_code = COUNTRY_CODES.get(city_key.lower(), 'en-gb')
    
    # Skapa hotellnamn-baserad sök-URL
    if hotel_id and hotel_name:
        hotel_name_encoded = quote_plus(hotel_name)
        
        base_params = {
            'ss': hotel_name,
            'dest_id': hotel_id,
            'dest_type': 'hotel',
            'checkin': checkin,
            'checkout': checkout,
            'group_adults': adults,
            'no_rooms': rooms,
            'group_children': 0,
            'search_selected': 'true'
        }
        
        if room_type and room_type in ROOM_TYPE_MAPPING:
            base_params['room_type'] = room_type
        
        params_string = '&'.join([f"{key}={quote_plus(str(value))}" 
                                for key, value in base_params.items()])
        
        return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"
    
    # Fallback URL
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={quote_plus(hotel_name)}"

def create_tripadvisor_url(tripadvisor_hotel: Optional[Dict], city_key: str, 
                          checkin: str, checkout: str, guests: int, 
                          fallback_name: str = "") -> str:
    """Skapa TripAdvisor URL"""
    if tripadvisor_hotel:
        hotel_id = tripadvisor_hotel.get('location_id', '')
        tripadvisor_location_id = TRIPADVISOR_LOCATIONS.get(city_key.lower(), '')
        
        if hotel_id and tripadvisor_location_id:
            # Skapa TripAdvisor hotell-URL med booking parametrar
            base_url = f"https://www.tripadvisor.com/Hotel_Review-g{tripadvisor_location_id}-d{hotel_id}"
            
            params = {
                'checkin': checkin,
                'checkout': checkout,
                'adults': str(guests),
                'rooms': '1'
            }
            
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            return f"{base_url}?{param_string}"
    
    # Fallback: Sök på TripAdvisor med hotellnamn
    search_query = quote_plus(f"{fallback_name} {city_key}")
    return f"https://www.tripadvisor.com/Search?q={search_query}"

def analyze_room_type_match(hotel: Dict, requested_room_type: Optional[str]) -> Optional[str]:
    """Analysera om hotellet matchar begärd rumstyp"""
    if not requested_room_type or requested_room_type not in ROOM_TYPE_MAPPING:
        return None
    
    hotel_name = hotel.get('name', '').lower()
    hotel_description = hotel.get('description', '').lower()
    
    type_keywords = {
        'single': ['single', 'solo', 'individual'],
        'double': ['double', 'couple', 'twin'],
        'family': ['family', 'connecting', 'adjoining', 'kids'],
        'junior_suite': ['junior suite', 'junior', 'sitting area', 'upgraded'],
        'suite': ['suite', 'apartment', 'kitchen', 'separate', 'premium']
    }
    
    keywords = type_keywords.get(requested_room_type, [])
    text_to_search = f"{hotel_name} {hotel_description}"
    
    for keyword in keywords:
        if keyword in text_to_search:
            return ROOM_TYPE_MAPPING[requested_room_type]["description"]
    
    return None

def process_dual_hotel_data(booking_hotels: List[Dict], tripadvisor_hotels: List[Dict],
                           city_key: str, checkin: str, checkout: str, 
                           adults: int, rooms: int, room_type: Optional[str] = None) -> List[Dict]:
    """Bearbeta hotelldata från BÅDA källorna"""
    processed_hotels = []
    
    for i, booking_hotel in enumerate(booking_hotels[:50]):
        try:
            # Extrahera Booking.com data
            hotel_name = booking_hotel.get('name', f'Hotel {i+1}')
            
            # Koordinater från Booking.com
            lat = booking_hotel.get('latitude')
            lng = booking_hotel.get('longitude')
            coordinates = [float(lat), float(lng)] if lat and lng else [0.0, 0.0]
            
            # Pris från Booking.com
            price = "Price on request"
            if 'priceBreakdown' in booking_hotel:
                price_info = booking_hotel['priceBreakdown'].get('grossPrice', {})
                if 'value' in price_info:
                    price = f"€{int(price_info['value'])}"
            elif 'price' in booking_hotel:
                price = f"€{booking_hotel['price']}"
            
            # Rating från Booking.com
            rating = float(booking_hotel.get('reviewScore', 4.0))
            if rating > 5:
                rating = rating / 2
            
            # Adress
            address = booking_hotel.get('address', city_key)
            
            # Hitta matchande TripAdvisor hotell
            matched_tripadvisor = find_tripadvisor_hotel_by_name(hotel_name, tripadvisor_hotels)
            
            # Reviews count från TripAdvisor (om matchning finns)
            reviews_count = None
            if matched_tripadvisor:
                reviews_count = int(matched_tripadvisor.get('num_reviews', 0))
            
            # Rumstyp-matchning
            room_match = analyze_room_type_match(booking_hotel, room_type)
            
            # Skapa URLs för BÅDA plattformarna
            booking_url = create_booking_url(
                booking_hotel, city_key, checkin, checkout, adults, rooms, room_type
            )
            
            tripadvisor_url = create_tripadvisor_url(
                matched_tripadvisor, city_key, checkin, checkout, adults, hotel_name
            )
            
            # Skapa hotel response
            hotel_data = {
                "id": booking_hotel.get('id', f'hotel_{i}'),
                "name": hotel_name,
                "address": address,
                "coordinates": coordinates,
                "price": price,
                "rating": rating,
                "booking_url": booking_url,
                "tripadvisor_url": tripadvisor_url,  # NY: TripAdvisor URL
                "reviews_count": reviews_count,
                "room_type_match": room_match
            }
            
            processed_hotels.append(hotel_data)
            
        except Exception as e:
            logger.error(f"Error processing hotel {i}: {e}")
            continue
    
    return processed_hotels

# Flask Routes
@app.route('/')
def root():
    """Root endpoint med API information"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Backend API - Dual Platform</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .feature { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 8px; }
            .new { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API - Dual Platform Edition</h1>
        <p>Flask backend for European hotel search with BOTH Booking.com AND TripAdvisor integration</p>
        
        <div class="new">
            <strong>🆕 NEW: Dual Platform Integration</strong><br>
            Every hotel now includes BOTH Booking.com booking links AND TripAdvisor review links
        </div>
        
        <div class="feature">
            <strong>✅ Features:</strong><br>
            • Hotel search from Booking.com<br>
            • TripAdvisor reviews and links<br>
            • Room type filtering with Junior Suite<br>
            • Localized booking URLs<br>
            • Smart hotel matching between platforms
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>POST /hotels</strong> - Search hotels with dual platform data<br>
            Parameters: city, checkin_date, checkout_date, guest_number, room_number, room_type<br>
            <em>Returns hotels with BOTH booking and TripAdvisor URLs</em>
        </div>
        <div class="endpoint">
            <strong>GET /room-types</strong> - List all available room types
        </div>
        <div class="endpoint">
            <strong>GET /cities</strong> - List all supported cities
        </div>
        <div class="endpoint">
            <strong>GET /test</strong> - Test both APIs with Stockholm
        </div>
        <div class="endpoint">
            <strong>GET /health</strong> - Health check
        </div>
        
        <h2>Data Sources:</h2>
        <p>✅ Booking.com (Primary hotel data + booking links)<br>
        ✅ TripAdvisor (Reviews + additional hotel links)</p>
        
        <h2>Supported Cities:</h2>
        <p>{{ cities|length }} European cities with dual platform support</p>
    </body>
    </html>
    ''', cities=TRIPADVISOR_LOCATIONS)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    api_key_valid = validate_api_key()
    
    return jsonify({
        "status": "healthy" if api_key_valid else "unhealthy",
        "api_key": "configured" if api_key_valid else "missing",
        "data_sources": ["Booking.com", "TripAdvisor"],
        "supported_cities": len(TRIPADVISOR_LOCATIONS),
        "room_types": list(ROOM_TYPE_MAPPING.keys()),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/hotels', methods=['POST'])
def search_hotels():
    """Sök hotell från BÅDA Booking.com OCH TripAdvisor"""
    
    # Validera API-nyckel
    if not validate_api_key():
        return jsonify({"error": "API service not configured properly"}), 503
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    # Extrahera parametrar
    city = data.get('city')
    checkin_date = data.get('checkin_date')
    checkout_date = data.get('checkout_date')
    guest_number = int(data.get('guest_number', 2))
    room_number = int(data.get('room_number', 1))
    room_type = data.get('room_type')
    
    if not all([city, checkin_date, checkout_date]):
        return jsonify({"error": "Missing required parameters: city, checkin_date, checkout_date"}), 400
    
    # Hämta Booking.com city ID
    booking_dest_id = get_city_id(city)
    if not booking_dest_id:
        return jsonify({"error": f"City '{city}' not found in Booking.com database"}), 404
    
    # Hämta TripAdvisor location ID
    tripadvisor_location_id = TRIPADVISOR_LOCATIONS.get(city.lower())
    
    # Validera rumstyp
    if room_type and room_type not in ROOM_TYPE_MAPPING:
        return jsonify({"error": f"Invalid room type. Available: {list(ROOM_TYPE_MAPPING.keys())}"}), 400
    
    try:
        # API-anrop till båda tjänsterna
        booking_data = search_hotels_booking_api(
            booking_dest_id, checkin_date, checkout_date, guest_number, room_number
        )
        
        tripadvisor_data = None
        if tripadvisor_location_id:
            tripadvisor_data = get_tripadvisor_hotels(tripadvisor_location_id)
        
        # Kontrollera Booking.com data
        if not booking_data or 'data' not in booking_data:
            return jsonify({"error": "No hotels found from Booking.com"}), 404
        
        booking_hotels = booking_data.get('data', [])
        tripadvisor_hotels = tripadvisor_data.get('data', []) if tripadvisor_data else []
        
        if not booking_hotels:
            return jsonify({"error": "No hotels found for the specified criteria"}), 404
        
        # Bearbeta data från BÅDA källor
        processed_hotels = process_dual_hotel_data(
            booking_hotels, tripadvisor_hotels, city,
            checkin_date, checkout_date, guest_number, room_number, room_type
        )
        
        # Skapa response
        return jsonify({
            "city": city,
            "hotels": processed_hotels,
            "total_found": len(processed_hotels),
            "search_params": {
                "checkin": checkin_date,
                "checkout": checkout_date,
                "guests": guest_number,
                "rooms": room_number
            },
            "room_filter": room_type,
            "data_sources": ["Booking.com", "TripAdvisor"],
            "booking_optimization": "enabled",
            "tripadvisor_integration": "enabled"
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": f"Service error: {str(e)}"}), 503

@app.route('/room-types', methods=['GET'])
def get_room_types():
    """Hämta tillgängliga rumstyper"""
    return jsonify({
        "room_types": ROOM_TYPE_MAPPING,
        "available_types": list(ROOM_TYPE_MAPPING.keys())
    })

@app.route('/cities', methods=['GET'])
def get_supported_cities():
    """Hämta alla städer som stöds"""
    cities = []
    for city_key, tripadvisor_id in TRIPADVISOR_LOCATIONS.items():
        booking_id = get_city_id(city_key)
        cities.append({
            "city": city_key,
            "booking_dest_id": booking_id,
            "tripadvisor_location_id": tripadvisor_id,
            "country_code": COUNTRY_CODES.get(city_key, "en-gb"),
            "both_platforms": bool(booking_id and tripadvisor_id)
        })
    
    return jsonify({
        "cities": cities,
        "total": len(cities),
        "dual_platform_cities": len([c for c in cities if c["both_platforms"]]),
        "data_sources": ["Booking.com", "TripAdvisor"]
    })

@app.route('/test', methods=['GET'])
def test_dual_integration():
    """Test endpoint för både Booking.com och TripAdvisor"""
    try:
        # Test Stockholm med båda API:er
        booking_data = search_hotels_booking_api("1371", "2025-07-20", "2025-07-22", 2, 1)
        tripadvisor_data = get_tripadvisor_hotels("189839", 5)
        
        booking_hotels = booking_data.get('data', []) if booking_data else []
        tripadvisor_hotels = tripadvisor_data.get('data', []) if tripadvisor_data else []
        
        if booking_hotels:
            processed = process_dual_hotel_data(
                booking_hotels[:3], tripadvisor_hotels,
                "stockholm", "2025-07-20", "2025-07-22", 2, 1
            )
            
            return jsonify({
                "status": "success",
                "test_city": "Stockholm",
                "booking_hotels_found": len(booking_hotels),
                "tripadvisor_hotels_found": len(tripadvisor_hotels),
                "sample_hotels": processed,
                "data_sources": ["Booking.com", "TripAdvisor"],
                "api_keys_working": True
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No Booking.com data found",
                "booking_response": booking_data,
                "tripadvisor_response": tripadvisor_data
            })
            
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Development server
if __name__ == "__main__":
    logger.info("Starting STAYFINDR Backend API v2.0 - Flask Dual Platform Edition")
    logger.info("Supporting BOTH Booking.com AND TripAdvisor integration")
    
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
