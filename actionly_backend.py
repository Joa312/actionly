# STAYFINDR BACKEND v11.0 - Dual API Integration
# Flask backend with Booking.com + TripAdvisor integration
# FIXED: Real TripAdvisor data + 71 cities from CSV

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
from concurrent.futures import ThreadPoolExecutor
import threading

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RapidAPI Configuration
RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
BOOKING_HOST = "booking-com18.p.rapidapi.com"
TRIPADVISOR_HOST = "tripadvisor16.p.rapidapi.com"

# Cache for TripAdvisor location IDs (to avoid repeated API calls)
TRIPADVISOR_LOCATION_CACHE = {}
cache_lock = threading.Lock()

# Country codes for Booking.com URLs
COUNTRY_CODES = {
    'stockholm': 'sv', 'gothenburg': 'sv', 'malmo': 'sv',
    'oslo': 'no', 'bergen': 'no',
    'helsinki': 'fi', 'tampere': 'fi',
    'copenhagen': 'dk', 'aarhus': 'dk',
    'paris': 'fr', 'lyon': 'fr', 'nice': 'fr', 'marseille': 'fr', 'bordeaux': 'fr',
    'london': 'en-gb', 'edinburgh': 'en-gb', 'manchester': 'en-gb', 'liverpool': 'en-gb',
    'amsterdam': 'nl', 'rotterdam': 'nl', 'utrecht': 'nl',
    'brussels': 'nl', 'antwerp': 'nl',
    'barcelona': 'es', 'madrid': 'es', 'palma': 'es', 'ibiza': 'es', 
    'valencia': 'es', 'seville': 'es', 'bilbao': 'es',
    'rome': 'it', 'milan': 'it', 'florence': 'it', 'venice': 'it', 'naples': 'it',
    'berlin': 'de', 'munich': 'de', 'hamburg': 'de', 'cologne': 'de', 'frankfurt': 'de',
    'vienna': 'de', 'salzburg': 'de',
    'zurich': 'de', 'geneva': 'fr', 'bern': 'de',
    'prague': 'cs', 'brno': 'cs',
    'warsaw': 'pl', 'krakow': 'pl',
    'budapest': 'hu', 'debrecen': 'hu',
    'dublin': 'en-gb', 'cork': 'en-gb',
    'lisbon': 'pt', 'porto': 'pt',
    'athens': 'el', 'santorini': 'el', 'mykonos': 'el', 'thessaloniki': 'el'
}

def load_cities_from_csv():
    """Load all cities from cities.csv file"""
    cities = {}
    csv_path = 'cities.csv'
    
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
                    logger.info(f"✅ Loaded city: {city_key} - {cities[city_key]['name']}")
        
        logger.info(f"✅ Loaded {len(cities)} cities from cities.csv")
        return cities
        
    except Exception as e:
        logger.error(f"❌ Error reading cities.csv: {e}")
        return get_fallback_cities()

def get_fallback_cities():
    """Minimal fallback cities if CSV fails"""
    return {
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
        }
    }

# Load cities at startup
CITIES = load_cities_from_csv()

# === BOOKING.COM API FUNCTIONS ===

def get_booking_location_id(city_info):
    """Get Booking.com location ID for a city"""
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {"query": city_info['search_query'], "languageCode": "en"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": BOOKING_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                location_id = data['data'][0].get('id')
                logger.info(f"✅ Booking location_id: {location_id} for {city_info['name']}")
                return location_id
    except Exception as e:
        logger.error(f"❌ Booking location ID error: {e}")
    
    return None

def search_booking_hotels(location_id, checkin, checkout, adults, rooms):
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
        "x-rapidapi-host": BOOKING_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            return data
    except Exception as e:
        logger.error(f"❌ Booking hotels search error: {e}")
    
    return None

# === TRIPADVISOR API FUNCTIONS ===

def get_tripadvisor_location_id(city_info):
    """Get TripAdvisor location ID for a city"""
    
    # Check cache first
    city_name = city_info['name']
    with cache_lock:
        if city_name in TRIPADVISOR_LOCATION_CACHE:
            logger.info(f"📦 Using cached TripAdvisor location ID for {city_name}")
            return TRIPADVISOR_LOCATION_CACHE[city_name]
    
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchLocation"
    
    querystring = {"query": city_info['search_query'].split(',')[0]}  # Just city name
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": TRIPADVISOR_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                location_id = data['data'][0].get('geoId')
                logger.info(f"✅ TripAdvisor location_id: {location_id} for {city_name}")
                
                # Cache the result
                with cache_lock:
                    TRIPADVISOR_LOCATION_CACHE[city_name] = location_id
                
                return location_id
    except Exception as e:
        logger.error(f"❌ TripAdvisor location ID error: {e}")
    
    return None

def search_tripadvisor_hotels(location_id, checkin, checkout, adults, rooms):
    """Search hotels using TripAdvisor API"""
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchHotels"
    
    querystring = {
        "geoId": location_id,
        "checkIn": checkin,
        "checkOut": checkout,
        "pageNumber": "1",
        "currencyCode": "EUR"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": TRIPADVISOR_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logger.error(f"❌ TripAdvisor API returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ TripAdvisor hotels search error: {e}")
    
    return None

def process_tripadvisor_hotels(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process TripAdvisor hotel data to match our format"""
    processed_hotels = []
    
    # Extract hotels from TripAdvisor response structure
    hotels = hotels_data.get('data', {}).get('data', [])
    
    for i, hotel in enumerate(hotels[:20]):  # Limit to 20 hotels
        try:
            # Extract hotel name
            hotel_name = hotel.get('title', 'Unknown Hotel')
            
            # Extract coordinates
            latitude = hotel.get('latitude')
            longitude = hotel.get('longitude')
            
            if latitude and longitude:
                coordinates = [float(latitude), float(longitude)]
            else:
                # Fallback to city center
                coordinates = city_info['coordinates']
            
            # Extract price
            price = 'N/A'
            price_details = hotel.get('priceDetails', {})
            if price_details:
                display_price = price_details.get('displayPrice', {})
                if isinstance(display_price, dict):
                    price_str = display_price.get('string', '')
                elif isinstance(display_price, str):
                    price_str = display_price
                else:
                    price_str = ''
                
                # Extract numeric price
                if price_str:
                    import re
                    numbers = re.findall(r'\d+', price_str.replace(',', ''))
                    if numbers:
                        price = int(numbers[0])
            
            # Extract rating
            rating = 4.0  # Default
            rating_info = hotel.get('bubbleRating', {})
            if rating_info:
                rating = float(rating_info.get('rating', 4.0))
            
            # Extract review count
            reviews_count = hotel.get('reviewCount', 0)
            
            # Build TripAdvisor URL
            hotel_id = hotel.get('id', '')
            tripadvisor_url = f"https://www.tripadvisor.com/Hotel_Review-g{hotel_id}.html"
            
            # Create booking search URL
            country_code = COUNTRY_CODES.get(city_key, 'en-gb')
            booking_url = f"https://www.booking.com/searchresults.{country_code}.html?ss={quote_plus(hotel_name)}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
            
            processed_hotel = {
                'id': f"ta_{hotel.get('id', i)}",
                'name': hotel_name,
                'address': hotel.get('address', city_info['name']),
                'coordinates': coordinates,
                'price': price,
                'rating': rating,
                'reviews_count': reviews_count,
                'booking_url': booking_url,
                'tripadvisor_url': tripadvisor_url,
                'source': 'tripadvisor',
                'provider_rank': hotel.get('rank', i + 1)
            }
            
            processed_hotels.append(processed_hotel)
            
        except Exception as e:
            logger.error(f"Error processing TripAdvisor hotel {i}: {e}")
            continue
    
    return processed_hotels

def create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key):
    """Create hotel booking URL"""
    # Get hotel name and ID
    hotel_id = hotel.get('id') or hotel.get('hotel_id')
    hotel_name = hotel.get('name', 'Hotel')
    
    # Get country code
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    
    # Create search URL with hotel name
    base_params = {
        'ss': hotel_name,
        'checkin': checkin,
        'checkout': checkout,
        'group_adults': adults,
        'no_rooms': rooms,
        'search_selected': 'true'
    }
    
    if hotel_id:
        base_params['dest_id'] = hotel_id
        base_params['dest_type'] = 'hotel'
    
    params_string = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in base_params.items()])
    
    return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"

def process_booking_hotels(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process Booking.com hotel data"""
    processed_hotels = []
    
    for i, hotel in enumerate(hotels_data):
        # Skip problematic Stockholm hotel in Germany
        hotel_name = hotel.get('name', 'Unknown Hotel')
        if city_key == 'stockholm' and 'stockholm' in hotel_name.lower() and len(hotel_name.split()) == 1:
            logger.warning(f"🔧 Filtering out German hotel 'Stockholm'")
            continue
        
        # Extract coordinates
        latitude = hotel.get('latitude')
        longitude = hotel.get('longitude')
        
        if latitude and longitude:
            coordinates = [float(latitude), float(longitude)]
        else:
            coordinates = city_info['coordinates']
        
        # Extract price
        price = 'N/A'
        if 'priceBreakdown' in hotel:
            price_info = hotel['priceBreakdown'].get('grossPrice', {})
            if 'value' in price_info:
                total_price = price_info['value']
                try:
                    checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
                    checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
                    nights = (checkout_date - checkin_date).days
                    if nights > 0:
                        price = int(total_price / nights)
                    else:
                        price = total_price
                except:
                    price = int(total_price / 7)
        
        # Extract rating
        rating = hotel.get('reviewScore', 4.0)
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)
        
        # Create booking URL
        booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key)
        
        processed_hotel = {
            'id': f"bk_{hotel.get('id', i)}",
            'name': hotel_name,
            'address': hotel.get('address', city_info['name']),
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'booking_url': booking_url,
            'source': 'booking',
            'provider_rank': i + 1
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels[:20]  # Limit to 20 hotels

# === API ENDPOINTS ===

@app.route('/')
def home():
    """API Documentation Page"""
    total_cities = len(CITIES)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Backend API v11.0</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .new { background: #d4edda; border-left: 4px solid #28a745; }
            .feature { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 8px; }
            .status { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ffc107; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API v11.0</h1>
        <p>Dual API Integration: Booking.com + TripAdvisor</p>
        
        <div class="status">
            <strong>🎯 v11.0 Features:</strong><br>
            ✅ Real TripAdvisor API integration (no more mock data!)<br>
            ✅ Parallel search from both Booking.com and TripAdvisor<br>
            ✅ {{total_cities}} European cities supported<br>
            ✅ Intelligent caching for better performance
        </div>
        
        <h2>API Endpoints:</h2>
        
        <div class="endpoint new">
            <strong>/api/hotels/dual</strong> - Get hotels from BOTH sources<br>
            Combines Booking.com + TripAdvisor results<br>
            <em>Returns up to 40 hotels (20 from each source)</em>
        </div>
        
        <div class="endpoint">
            <strong>/api/hotels/booking</strong> - Booking.com hotels only<br>
            Parameters: city, checkin, checkout, adults, rooms
        </div>
        
        <div class="endpoint">
            <strong>/api/hotels/tripadvisor</strong> - TripAdvisor hotels only<br>
            Parameters: city, checkin, checkout, adults, rooms
        </div>
        
        <div class="endpoint">
            <strong>/api/cities</strong> - List all {{total_cities}} cities
        </div>
        
        <div class="endpoint">
            <strong>/test</strong> - Test dual API with Stockholm
        </div>
        
        <div class="feature">
            <strong>Performance Features:</strong><br>
            • Location ID caching reduces API calls<br>
            • Parallel API requests for faster results<br>
            • Automatic fallback if one API fails
        </div>
    </body>
    </html>
    ''', total_cities=total_cities)

@app.route('/api/cities')
def get_cities():
    """Get all supported cities"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES),
        'source': 'cities.csv'
    })

@app.route('/api/hotels/booking')
def get_booking_hotels():
    """Get only Booking.com hotels"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-20')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    
    # Get Booking.com location ID
    location_id = get_booking_location_id(city_info)
    if not location_id:
        return jsonify({'error': f'Could not find Booking.com location for {city}'}), 404
    
    # Search hotels
    hotels_data = search_booking_hotels(location_id, checkin, checkout, adults, rooms)
    if not hotels_data or 'data' not in hotels_data:
        return jsonify({'error': 'No hotels found on Booking.com'}), 404
    
    # Process hotels
    processed_hotels = process_booking_hotels(
        hotels_data['data'][:20], 
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
            'rooms': rooms
        },
        'data_source': 'booking'
    })

@app.route('/api/hotels/tripadvisor')
def get_tripadvisor_hotels():
    """Get only TripAdvisor hotels"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-20')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    
    # Get TripAdvisor location ID
    location_id = get_tripadvisor_location_id(city_info)
    if not location_id:
        return jsonify({'error': f'Could not find TripAdvisor location for {city}'}), 404
    
    # Search hotels
    hotels_data = search_tripadvisor_hotels(location_id, checkin, checkout, adults, rooms)
    if not hotels_data:
        return jsonify({'error': 'No hotels found on TripAdvisor'}), 404
    
    # Process hotels
    processed_hotels = process_tripadvisor_hotels(
        hotels_data, 
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
            'rooms': rooms
        },
        'data_source': 'tripadvisor'
    })

@app.route('/api/hotels/dual')
def get_dual_hotels():
    """Get hotels from BOTH Booking.com and TripAdvisor"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-20')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    all_hotels = []
    errors = []
    
    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both API calls
        booking_future = executor.submit(
            fetch_booking_hotels, 
            city_info, city, checkin, checkout, adults, rooms
        )
        tripadvisor_future = executor.submit(
            fetch_tripadvisor_hotels,
            city_info, city, checkin, checkout, adults, rooms
        )
        
        # Get Booking.com results
        try:
            booking_hotels = booking_future.result(timeout=10)
            all_hotels.extend(booking_hotels)
            logger.info(f"✅ Got {len(booking_hotels)} hotels from Booking.com")
        except Exception as e:
            logger.error(f"❌ Booking.com error: {e}")
            errors.append(f"Booking.com: {str(e)}")
        
        # Get TripAdvisor results
        try:
            tripadvisor_hotels = tripadvisor_future.result(timeout=10)
            all_hotels.extend(tripadvisor_hotels)
            logger.info(f"✅ Got {len(tripadvisor_hotels)} hotels from TripAdvisor")
        except Exception as e:
            logger.error(f"❌ TripAdvisor error: {e}")
            errors.append(f"TripAdvisor: {str(e)}")
    
    # Sort by rating (best first)
    all_hotels.sort(key=lambda x: x.get('rating', 0), reverse=True)
    
    return jsonify({
        'city': city_info['name'],
        'hotels': all_hotels,
        'total_found': len(all_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms
        },
        'data_source': 'dual',
        'sources': {
            'booking': len([h for h in all_hotels if h['source'] == 'booking']),
            'tripadvisor': len([h for h in all_hotels if h['source'] == 'tripadvisor'])
        },
        'errors': errors if errors else None
    })

def fetch_booking_hotels(city_info, city_key, checkin, checkout, adults, rooms):
    """Helper function to fetch Booking.com hotels"""
    location_id = get_booking_location_id(city_info)
    if not location_id:
        raise Exception(f"No Booking.com location ID for {city_info['name']}")
    
    hotels_data = search_booking_hotels(location_id, checkin, checkout, adults, rooms)
    if not hotels_data or 'data' not in hotels_data:
        return []
    
    return process_booking_hotels(
        hotels_data['data'][:20],
        city_info,
        checkin,
        checkout,
        adults,
        rooms,
        city_key
    )

def fetch_tripadvisor_hotels(city_info, city_key, checkin, checkout, adults, rooms):
    """Helper function to fetch TripAdvisor hotels"""
    location_id = get_tripadvisor_location_id(city_info)
    if not location_id:
        raise Exception(f"No TripAdvisor location ID for {city_info['name']}")
    
    hotels_data = search_tripadvisor_hotels(location_id, checkin, checkout, adults, rooms)
    if not hotels_data:
        return []
    
    return process_tripadvisor_hotels(
        hotels_data,
        city_info,
        checkin,
        checkout,
        adults,
        rooms,
        city_key
    )

@app.route('/test')
def test_dual():
    """Test endpoint with Stockholm hotels from both sources"""
    return get_dual_hotels()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend v11.0...")
    print(f"📊 Loaded {len(CITIES)} cities from CSV")
    print("🔧 Dual API integration: Booking.com + TripAdvisor")
    print("✅ Real TripAdvisor data - no more mocks!")
    print("⚡ Parallel API calls for better performance")
    print("🌍 Ready to serve all European cities!")
    
    # Use PORT environment variable for deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
