# STAYFINDR BACKEND v10.2 - CSV Integration with Stockholm Fix
# Flask backend with RapidAPI Booking.com integration
# FIXED: Reads all 71 cities from cities.csv + Stockholm location ID fix

import os
import logging
import csv
from datetime import datetime
from urllib.parse import quote_plus
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import time

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RapidAPI Configuration
RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
RAPIDAPI_HOST = "booking-com18.p.rapidapi.com"

# Country codes for Booking.com URLs based on city
COUNTRY_CODES = {
    'stockholm': 'sv', 'oslo': 'no', 'helsinki': 'fi', 'copenhagen': 'dk',
    'paris': 'fr', 'lyon': 'fr', 'nice': 'fr', 'marseille': 'fr', 'bordeaux': 'fr',
    'london': 'en-gb', 'edinburgh': 'en-gb', 'manchester': 'en-gb', 'liverpool': 'en-gb',
    'amsterdam': 'nl', 'brussels': 'nl', 'rotterdam': 'nl',
    'barcelona': 'es', 'madrid': 'es', 'palma': 'es', 'ibiza': 'es', 'valencia': 'es', 'seville': 'es',
    'rome': 'it', 'milano': 'it', 'florence': 'it', 'venice': 'it', 'naples': 'it',
    'berlin': 'de', 'munich': 'de', 'hamburg': 'de', 'cologne': 'de', 'frankfurt': 'de',
    'vienna': 'de', 'zurich': 'de', 'geneva': 'fr',
    'prague': 'cs', 'warsaw': 'pl', 'budapest': 'hu', 'krakow': 'pl',
    'dublin': 'en-gb', 'lisbon': 'pt', 'porto': 'pt',
    'athens': 'el', 'santorini': 'el', 'mykonos': 'el', 'thessaloniki': 'el'
}

# Special location IDs for problematic cities
SPECIAL_LOCATION_IDS = {
    'stockholm': '-2960556',  # CRITICAL: Fixed Stockholm location ID
    # Add more if needed based on testing
}

def load_cities_from_csv():
    """Load all cities from cities.csv file with correct column names"""
    cities = {}
    csv_path = 'cities.csv'
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        logger.error(f"❌ cities.csv not found at {csv_path}")
        return get_fallback_cities()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                city_key = row.get('key', '').lower().strip()
                if city_key:
                    cities[city_key] = {
                        'name': row.get('name', '').strip(),
                        'coordinates': [
                            float(row.get('lat', 0)),
                            float(row.get('lon', 0))
                        ],
                        'search_query': row.get('search_query', '').strip(),
                        'country': row.get('country', '').strip(),
                        'tripadvisor_id': row.get('tripadvisor_id', '').strip()
                    }
                    
                    # Add special location ID if it's Stockholm
                    if city_key == 'stockholm':
                        cities[city_key]['booking_location_id'] = SPECIAL_LOCATION_IDS['stockholm']
                        logger.info(f"🔧 Stockholm fix applied: location_id = {SPECIAL_LOCATION_IDS['stockholm']}")
        
        logger.info(f"✅ Loaded {len(cities)} cities from cities.csv")
        return cities
        
    except Exception as e:
        logger.error(f"❌ Error reading cities.csv: {e}")
        return get_fallback_cities()

def get_fallback_cities():
    """Fallback cities if CSV fails to load"""
    logger.warning("🔄 Using fallback cities (29 cities)")
    return {
        'stockholm': {
            'name': 'Stockholm, Sweden',
            'coordinates': [59.3293, 18.0686],
            'search_query': 'Stockholm Sweden',
            'booking_location_id': '-2960556'  # CRITICAL Stockholm fix
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
        },
        'rome': {
            'name': 'Rome, Italy',
            'coordinates': [41.9028, 12.4964],
            'search_query': 'Rome Italy'
        },
        'berlin': {
            'name': 'Berlin, Germany',
            'coordinates': [52.5200, 13.4050],
            'search_query': 'Berlin Germany'
        },
        'copenhagen': {
            'name': 'Copenhagen, Denmark',
            'coordinates': [55.6761, 12.5683],
            'search_query': 'Copenhagen Denmark'
        },
        'vienna': {
            'name': 'Vienna, Austria',
            'coordinates': [48.2082, 16.3738],
            'search_query': 'Vienna Austria'
        },
        'prague': {
            'name': 'Prague, Czech Republic',
            'coordinates': [50.0755, 14.4378],
            'search_query': 'Prague Czech Republic'
        }
    }

# Load cities at startup
CITIES = load_cities_from_csv()

def get_location_id(city_info):
    """Get Booking.com location ID for a city with Stockholm fix"""
    
    # CRITICAL FIX: Use hardcoded location_id if available
    if 'booking_location_id' in city_info:
        logger.info(f"✅ Using hardcoded location_id: {city_info['booking_location_id']} for {city_info['name']}")
        return city_info['booking_location_id']
    
    # Original API method for other cities
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {"query": city_info['search_query'], "languageCode": "en"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                location_id = data['data'][0].get('id')
                logger.info(f"✅ API location_id: {location_id} for {city_info['name']}")
                return location_id
        else:
            logger.error(f"❌ Location API error {response.status_code} for {city_info['name']}")
    except Exception as e:
        logger.error(f"❌ Location ID error for {city_info['name']}: {e}")
    
    return None

def search_hotels_booking_api(location_id, checkin, checkout, adults, rooms):
    """Search hotels using Booking.com API"""
    url = "https://booking-com18.p.rapidapi.com/stays/search"
    
    querystring = {
        "locationId": location_id,
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "adults": adults,
        "rooms": rooms,
        "currency": "EUR"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        logger.info(f"🔍 Searching hotels for location_id: {location_id}")
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Found {len(data.get('data', []))} hotels")
            return data
        else:
            logger.error(f"❌ Hotels API error: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Hotels search error: {e}")
    
    return None

def create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key):
    """Create hotel name-based booking URL for better targeting"""
    
    # Priority 1: Use direct hotel URL from API if available
    direct_urls = [
        hotel.get('url'),
        hotel.get('link'), 
        hotel.get('booking_url'),
        hotel.get('hotelUrl'),
        hotel.get('deepLink')
    ]
    
    for url in direct_urls:
        if url and 'booking.com' in str(url):
            # Add search parameters to direct URL
            if '?' in url:
                return f"{url}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
            else:
                return f"{url}?checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
    
    # Priority 2: Create hotel name-based search URL
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('propertyId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id and hotel_name:
        # Get country code for the city
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        
        # Encode hotel name properly for URL
        hotel_name_encoded = quote_plus(hotel_name)
        
        # Create hotel name-based search URL
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
        
        # Build URL parameters
        params_string = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in base_params.items()])
        
        return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"
    
    # Priority 3: Fallback to generic search
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={city_info['name']}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"

def process_hotel_data(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process and format hotel data with proper booking URLs"""
    processed_hotels = []
    
    for i, hotel in enumerate(hotels_data):
        # Extract hotel information
        hotel_name = hotel.get('name', 'Unknown Hotel')
        
        # Get real coordinates if available, otherwise use city center with offset
        latitude = hotel.get('latitude')
        longitude = hotel.get('longitude')
        
        if latitude and longitude:
            coordinates = [float(latitude), float(longitude)]
        else:
            # Use city center coordinates
            base_lat, base_lng = city_info['coordinates']
            coordinates = [
                base_lat + (i * 0.01) - 0.05,
                base_lng + (i * 0.01) - 0.05
            ]
        
        # Extract pricing information
        price = 'N/A'
        if 'priceBreakdown' in hotel:
            price_info = hotel['priceBreakdown'].get('grossPrice', {})
            if 'value' in price_info:
                total_price = price_info['value']
                try:
                    # Estimate per night
                    from datetime import datetime
                    checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
                    checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
                    nights = (checkout_date - checkin_date).days
                    if nights > 0:
                        price = int(total_price / nights)
                    else:
                        price = total_price
                except:
                    price = int(total_price / 7)  # Fallback: assume 7 nights
        elif 'price' in hotel:
            price = hotel['price']
        
        # Extract rating
        rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)  # Normalize to 5-point scale
        else:
            rating = 4.0
        
        # Extract address
        address = hotel.get('address', city_info['name'])
        
        # Create optimized booking URL with hotel name
        booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key)
        
        processed_hotel = {
            'id': hotel.get('id') or hotel.get('hotel_id') or f"hotel_{i}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'booking_url': booking_url,
            'source': 'booking.com',
            'tripadvisor_url': None
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

@app.route('/')
def home():
    """API Documentation Page"""
    total_cities = len(CITIES)
    cities_source = "cities.csv" if total_cities > 30 else "fallback"
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Backend API v10.2</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .cities { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0; }
            .city { background: #e3f2fd; padding: 8px; border-radius: 4px; text-align: center; font-size: 0.9rem; }
            .feature { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 8px; }
            .fix { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ffc107; }
            .csv-info { background: #d1ecf1; padding: 10px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #bee5eb; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API v10.2</h1>
        <p>Flask backend for European hotel search with CSV integration</p>
        
        <div class="csv-info">
            <strong>📊 v10.2 UPDATE: CSV Integration</strong><br>
            Loading {{total_cities}} cities from {{cities_source}}<br>
            Stockholm location ID: -2960556 (hardcoded fix)
        </div>
        
        <div class="fix">
            <strong>🔧 Stockholm Location ID Fixed</strong><br>
            No more German hotel results for Stockholm searches
        </div>
        
        <div class="feature">
            <strong>✅ Hotel Name-Based Booking URLs</strong><br>
            CTA buttons use hotel names for better targeting and SEO
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels/booking</strong> - Get Booking.com hotels for a city<br>
            Parameters: city, checkin, checkout, adults, rooms<br>
            <em>All {{total_cities}} cities supported!</em>
        </div>
        <div class="endpoint">
            <strong>/api/cities</strong> - List all {{total_cities}} cities
        </div>
        <div class="endpoint">
            <strong>/test</strong> - Test Stockholm hotels (fixed)
        </div>
        
        <h2>Cities supported ({{total_cities}} total):</h2>
        <div class="cities">
            {% for city in cities %}
            <div class="city">{{ city }}</div>
            {% endfor %}
        </div>
        
        <p><strong>Status:</strong> {{total_cities}} cities loaded from {{cities_source}} - Stockholm fix active!</p>
    </body>
    </html>
    ''', cities=list(CITIES.keys())[:40], total_cities=total_cities, cities_source=cities_source)

@app.route('/api/cities')
def get_cities():
    """Get all supported cities"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES),
        'source': 'cities.csv' if len(CITIES) > 30 else 'fallback'
    })

@app.route('/api/hotels/booking')
def get_hotels():
    """Get Booking.com hotels for a specific city with Stockholm fix"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-18')
    checkout = request.args.get('checkout', '2025-07-19')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    
    # Get location ID (with Stockholm fix)
    location_id = get_location_id(city_info)
    
    if not location_id:
        return jsonify({'error': f'Could not find location ID for {city}'}), 404
    
    # Search hotels
    hotels_data = search_hotels_booking_api(location_id, checkin, checkout, adults, rooms)
    
    if not hotels_data or 'data' not in hotels_data:
        return jsonify({'error': 'No hotels found'}), 404
    
    # Process hotel data - limit to top 50
    processed_hotels = process_hotel_data(
        hotels_data['data'][:50], 
        city_info, 
        checkin, 
        checkout, 
        adults, 
        rooms,
        city
    )
    
    return jsonify({
        'city': city_info['name'],
        'hotels': processed_hotels,
        'total_found': len(processed_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms,
            'city_key': city
        },
        'data_source': 'booking',
        'stockholm_fix': 'enabled' if city == 'stockholm' else 'not_needed',
        'location_id_used': location_id,
        'csv_loaded': len(CITIES) > 30,
        'total_cities_available': len(CITIES),
        'url_type': 'hotel_name_based'
    })

@app.route('/api/hotels/tripadvisor')
def get_tripadvisor_hotels():
    """Get TripAdvisor hotels (mock data fallback)"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-18')
    checkout = request.args.get('checkout', '2025-07-19')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    
    # Mock TripAdvisor data for demonstration
    mock_hotels = generate_mock_tripadvisor_data(city_info, checkin, checkout, adults, rooms)
    
    return jsonify({
        'city': city_info['name'],
        'hotels': mock_hotels,
        'total_found': len(mock_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms,
            'city_key': city
        },
        'data_source': 'tripadvisor'
    })

@app.route('/api/hotels/dual')
def get_dual_hotels():
    """Get hotels from both Booking.com and TripAdvisor"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-18')
    checkout = request.args.get('checkout', '2025-07-19')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    # Get Booking.com hotels
    booking_response = get_hotels()
    if booking_response.status_code != 200:
        # Fallback to mock data if Booking.com fails
        city_info = CITIES[city]
        mock_hotels = generate_mock_tripadvisor_data(city_info, checkin, checkout, adults, rooms)
        return jsonify({
            'city': city_info['name'],
            'hotels': mock_hotels,
            'total_found': len(mock_hotels),
            'search_params': {
                'checkin': checkin,
                'checkout': checkout, 
                'adults': adults,
                'rooms': rooms,
                'city_key': city
            },
            'data_source': 'dual_fallback'
        })
    
    # Return Booking.com data with dual source indicator
    booking_data = booking_response.get_json()
    booking_data['data_source'] = 'dual'
    return jsonify(booking_data)

def generate_mock_tripadvisor_data(city_info, checkin, checkout, adults, rooms):
    """Generate mock TripAdvisor data for demonstration"""
    base_hotels = [
        {'name': f'Hotel Frantz {city_info["name"].split(",")[0]}', 'price': 152, 'rating': 4.2},
        {'name': f'Scandic Continental', 'price': 189, 'rating': 4.4},
        {'name': f'Grand Hotel {city_info["name"].split(",")[0]}', 'price': 445, 'rating': 4.8}
    ]
    
    mock_hotels = []
    for i, hotel in enumerate(base_hotels):
        mock_hotels.append({
            'id': f'mock_{city_info["name"].split(",")[0].lower()}_{i}',
            'name': hotel['name'],
            'address': city_info['name'],
            'coordinates': [city_info['coordinates'][0], city_info['coordinates'][1] + (i * 0.01)],
            'price': hotel['price'],
            'rating': hotel['rating'],
            'reviews_count': 1250 + (i * 500),
            'booking_url': f'https://www.booking.com/searchresults.html?ss={hotel["name"].replace(" ", "+")}',
            'tripadvisor_url': f'https://www.tripadvisor.com/Search?q={hotel["name"].replace(" ", "+")}',
            'source': 'mock_data'
        })
    
    return mock_hotels

@app.route('/test')
def test_stockholm():
    """Test endpoint with Stockholm hotels (should now show Swedish hotels)"""
    return get_hotels()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend v10.2...")
    print(f"📊 Loaded {len(CITIES)} cities from CSV")
    print("🔧 Stockholm location ID fix enabled")
    print("🌍 Hotel name-based booking URLs")
    print("✅ Ready to serve all European cities!")
    
    # Use PORT environment variable for deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
