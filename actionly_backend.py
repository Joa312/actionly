#!/usr/bin/env python3
"""
STAYFINDR Backend API - Fixad Flask Version
European Hotel Search Engine med förbättrad felhantering
"""

import os
import logging
import json
from datetime import datetime
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

# Flask app
app = Flask(__name__)
CORS(app)

# API konfiguration
API_KEY = os.getenv("RAPIDAPI_KEY", "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999")

# Förbättrade headers för båda API:er
BOOKING_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
}

TRIPADVISOR_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "tripadvisor1.p.rapidapi.com"
}

# Fallback städer för Booking.com (om CSV saknas)
FALLBACK_CITIES = {
    'stockholm': '1371',
    'paris': '-1456928',
    'london': '-2601889',
    'barcelona': '-372490',
    'rome': '-126693',
    'amsterdam': '-2140479',
    'berlin': '-1746443',
    'copenhagen': '-2745240',
    'vienna': '-1995499',
    'prague': '-553173',
    'madrid': '-390625',
    'milan': '-121726'
}

# TripAdvisor location IDs
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
    'milan': '187849'
}

# Country codes för lokaliserade URLs
COUNTRY_CODES = {
    'stockholm': 'sv', 'paris': 'fr', 'london': 'en-gb', 'barcelona': 'es',
    'rome': 'it', 'amsterdam': 'nl', 'berlin': 'de', 'copenhagen': 'dk',
    'vienna': 'de', 'prague': 'cs', 'madrid': 'es', 'milan': 'it'
}

def validate_api_key():
    """Kontrollera API-nyckel"""
    if not API_KEY or API_KEY == "YOUR_RAPIDAPI_KEY":
        logger.error("❌ API key saknas eller är inte konfigurerad")
        return False
    logger.info(f"✅ API key konfigurerad: {API_KEY[:10]}...")
    return True

def get_booking_city_id(city: str) -> str:
    """Hämta Booking.com city ID"""
    city_lower = city.lower()
    city_id = FALLBACK_CITIES.get(city_lower)
    
    if city_id:
        logger.info(f"✅ Hittade Booking.com ID för {city}: {city_id}")
    else:
        logger.warning(f"❌ Staden {city} stöds inte")
    
    return city_id

def search_booking_hotels(dest_id: str, checkin: str, checkout: str, adults: int, rooms: int):
    """Sök hotell från Booking.com med förbättrad felhantering"""
    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
    
    params = {
        "dest_id": dest_id,
        "dest_type": "city", 
        "checkin_date": checkin,
        "checkout_date": checkout,
        "room_number": rooms,
        "guest_number": adults,
        "locale": "en-gb",
        "currency": "EUR",
        "order_by": "popularity"
    }
    
    logger.info(f"🔍 Booking.com API anrop: {url}")
    logger.info(f"📋 Parametrar: {params}")
    
    try:
        response = requests.get(url, headers=BOOKING_HEADERS, params=params, timeout=15)
        
        logger.info(f"📡 Booking.com svar: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            hotels = data.get('data', [])
            logger.info(f"✅ Booking.com: {len(hotels)} hotell hittade")
            return data
        else:
            logger.error(f"❌ Booking.com API fel: {response.status_code}")
            logger.error(f"❌ Svar: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("❌ Booking.com API timeout")
        return None
    except Exception as e:
        logger.error(f"❌ Booking.com fel: {e}")
        return None

def search_tripadvisor_hotels(location_id: str):
    """Sök hotell från TripAdvisor"""
    url = "https://tripadvisor1.p.rapidapi.com/hotels/list"
    
    params = {
        "location_id": location_id,
        "limit": "20",
        "sort": "recommended",
        "offset": "0",
        "currency": "EUR",
        "lang": "en_US"
    }
    
    logger.info(f"🔍 TripAdvisor API anrop: {url}")
    
    try:
        response = requests.get(url, headers=TRIPADVISOR_HEADERS, params=params, timeout=15)
        
        logger.info(f"📡 TripAdvisor svar: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            hotels = data.get('data', [])
            logger.info(f"✅ TripAdvisor: {len(hotels)} hotell hittade")
            return data
        else:
            logger.error(f"❌ TripAdvisor API fel: {response.status_code}")
            logger.error(f"❌ Svar: {response.text[:200]}")
            return None
            
    except Exception as e:
        logger.error(f"❌ TripAdvisor fel: {e}")
        return None

def create_booking_url(hotel, city_key, checkin, checkout, adults, rooms):
    """Skapa Booking.com URL"""
    hotel_name = hotel.get('name', 'Hotel')
    hotel_id = hotel.get('id', '')
    country_code = COUNTRY_CODES.get(city_key.lower(), 'en-gb')
    
    if hotel_id and hotel_name:
        base_params = {
            'ss': hotel_name,
            'dest_id': hotel_id,
            'dest_type': 'hotel',
            'checkin': checkin,
            'checkout': checkout,
            'group_adults': adults,
            'no_rooms': rooms,
            'search_selected': 'true'
        }
        
        params_string = '&'.join([f"{key}={quote_plus(str(value))}" 
                                for key, value in base_params.items()])
        
        return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"
    
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={quote_plus(hotel_name)}"

def create_tripadvisor_url(hotel_name, city_key, tripadvisor_id=None):
    """Skapa TripAdvisor URL"""
    if tripadvisor_id:
        city_location_id = TRIPADVISOR_LOCATIONS.get(city_key.lower(), '')
        if city_location_id:
            return f"https://www.tripadvisor.com/Hotel_Review-g{city_location_id}-d{tripadvisor_id}"
    
    # Fallback: Sök på TripAdvisor
    search_query = quote_plus(f"{hotel_name} {city_key}")
    return f"https://www.tripadvisor.com/Search?q={search_query}"

def process_hotel_data(booking_hotels, tripadvisor_hotels, city_key, checkin, checkout, adults, rooms):
    """Bearbeta hotelldata från båda källorna"""
    processed_hotels = []
    
    for i, hotel in enumerate(booking_hotels[:20]):
        try:
            hotel_name = hotel.get('name', f'Hotel {i+1}')
            
            # Koordinater
            lat = hotel.get('latitude', 0)
            lng = hotel.get('longitude', 0)
            coordinates = [float(lat), float(lng)] if lat and lng else [0.0, 0.0]
            
            # Pris
            price = "Price on request"
            if 'priceBreakdown' in hotel:
                price_info = hotel['priceBreakdown'].get('grossPrice', {})
                if 'value' in price_info:
                    price = f"€{int(price_info['value'])}"
            elif 'price' in hotel:
                price = f"€{hotel['price']}"
            
            # Rating
            rating = float(hotel.get('reviewScore', 4.0))
            if rating > 5:
                rating = rating / 2
            
            # Adress
            address = hotel.get('address', city_key)
            
            # Skapa URLs
            booking_url = create_booking_url(hotel, city_key, checkin, checkout, adults, rooms)
            tripadvisor_url = create_tripadvisor_url(hotel_name, city_key)
            
            # Hitta recensioner från TripAdvisor (om möjligt)
            reviews_count = None
            for ta_hotel in tripadvisor_hotels:
                if hotel_name.lower() in ta_hotel.get('name', '').lower():
                    reviews_count = ta_hotel.get('num_reviews', 0)
                    tripadvisor_url = create_tripadvisor_url(
                        hotel_name, city_key, ta_hotel.get('location_id')
                    )
                    break
            
            processed_hotels.append({
                "id": hotel.get('id', f'hotel_{i}'),
                "name": hotel_name,
                "address": address,
                "coordinates": coordinates,
                "price": price,
                "rating": rating,
                "booking_url": booking_url,
                "tripadvisor_url": tripadvisor_url,
                "reviews_count": reviews_count
            })
            
        except Exception as e:
            logger.error(f"❌ Fel vid bearbetning av hotell {i}: {e}")
            continue
    
    return processed_hotels

# Flask Routes
@app.route('/')
def root():
    """Startsida"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Backend - Dual Platform</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .status { background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API</h1>
        <p>Flask backend med BÅDE Booking.com OCH TripAdvisor integration</p>
        
        <div class="status">
            <strong>✅ Backend Status:</strong><br>
            Flask server är live och redo för hotellsökningar!
        </div>
        
        <h2>Endpoints:</h2>
        <div class="endpoint">
            <strong>GET /test</strong> - Testa båda API:erna med Stockholm
        </div>
        <div class="endpoint">
            <strong>POST /hotels</strong> - Sök hotell med dual platform data
        </div>
        <div class="endpoint">
            <strong>GET /health</strong> - Health check
        </div>
        
        <p><strong>Supported cities:</strong> {{ cities|length }} europeiska städer</p>
        <p><strong>Data sources:</strong> Booking.com + TripAdvisor</p>
    </body>
    </html>
    ''', cities=FALLBACK_CITIES)

@app.route('/health')
def health():
    """Health check med detaljerad information"""
    api_valid = validate_api_key()
    
    return jsonify({
        "status": "healthy" if api_valid else "unhealthy",
        "api_key_configured": api_valid,
        "api_key_preview": f"{API_KEY[:10]}..." if API_KEY else "None",
        "supported_cities": len(FALLBACK_CITIES),
        "tripadvisor_cities": len(TRIPADVISOR_LOCATIONS),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test')
def test():
    """Test endpoint med detaljerad information"""
    logger.info("🧪 Startar test av båda API:erna...")
    
    # Kontrollera API-nyckel
    if not validate_api_key():
        return jsonify({
            "status": "error",
            "message": "API key inte konfigurerad",
            "api_key_preview": f"{API_KEY[:10]}..." if API_KEY else "None"
        })
    
    # Test Stockholm
    booking_dest_id = get_booking_city_id("stockholm")
    tripadvisor_location_id = TRIPADVISOR_LOCATIONS.get("stockholm")
    
    if not booking_dest_id:
        return jsonify({
            "status": "error",
            "message": "Stockholm inte hittad i Booking.com data"
        })
    
    # Testa Booking.com
    logger.info("🔍 Testar Booking.com API...")
    booking_data = search_booking_hotels(booking_dest_id, "2025-07-20", "2025-07-22", 2, 1)
    
    # Testa TripAdvisor
    logger.info("🔍 Testar TripAdvisor API...")
    tripadvisor_data = search_tripadvisor_hotels(tripadvisor_location_id) if tripadvisor_location_id else None
    
    # Resultat
    booking_hotels = booking_data.get('data', []) if booking_data else []
    tripadvisor_hotels = tripadvisor_data.get('data', []) if tripadvisor_data else []
    
    if booking_hotels:
        processed = process_hotel_data(
            booking_hotels[:3], tripadvisor_hotels, 
            "stockholm", "2025-07-20", "2025-07-22", 2, 1
        )
        
        return jsonify({
            "status": "success",
            "message": "Båda API:erna fungerar!",
            "booking_hotels_found": len(booking_hotels),
            "tripadvisor_hotels_found": len(tripadvisor_hotels),
            "sample_hotels": processed,
            "api_key_working": True
        })
    else:
        return jsonify({
            "status": "error", 
            "message": "Ingen data från Booking.com",
            "booking_response_status": "error" if not booking_data else "empty",
            "tripadvisor_response_status": "error" if not tripadvisor_data else "empty",
            "api_key_preview": f"{API_KEY[:10]}..."
        })

@app.route('/hotels', methods=['POST'])
def search_hotels():
    """Sök hotell från båda plattformarna"""
    
    if not validate_api_key():
        return jsonify({"error": "API inte konfigurerad"}), 503
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data krävs"}), 400
    
    city = data.get('city', '').lower()
    checkin = data.get('checkin_date')
    checkout = data.get('checkout_date')
    adults = int(data.get('guest_number', 2))
    rooms = int(data.get('room_number', 1))
    
    if not all([city, checkin, checkout]):
        return jsonify({"error": "city, checkin_date och checkout_date krävs"}), 400
    
    # Hämta city IDs
    booking_id = get_booking_city_id(city)
    tripadvisor_id = TRIPADVISOR_LOCATIONS.get(city)
    
    if not booking_id:
        return jsonify({"error": f"Staden {city} stöds inte"}), 404
    
    try:
        # Sök på båda plattformarna
        booking_data = search_booking_hotels(booking_id, checkin, checkout, adults, rooms)
        tripadvisor_data = search_tripadvisor_hotels(tripadvisor_id) if tripadvisor_id else None
        
        if not booking_data or not booking_data.get('data'):
            return jsonify({"error": "Inga hotell hittade"}), 404
        
        booking_hotels = booking_data['data']
        tripadvisor_hotels = tripadvisor_data.get('data', []) if tripadvisor_data else []
        
        # Bearbeta data
        processed = process_hotel_data(
            booking_hotels, tripadvisor_hotels, city, checkin, checkout, adults, rooms
        )
        
        return jsonify({
            "city": city.title(),
            "hotels": processed,
            "total_found": len(processed),
            "search_params": {
                "checkin": checkin,
                "checkout": checkout,
                "guests": adults,
                "rooms": rooms
            },
            "data_sources": ["Booking.com", "TripAdvisor"]
        })
        
    except Exception as e:
        logger.error(f"❌ Sökfel: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("🚀 Startar STAYFINDR Flask Backend...")
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
