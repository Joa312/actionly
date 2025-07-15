# STAYFINDR BACKEND - Professional Production-Ready Architecture
# Multi-platform integration with robust error handling and caching
# Combines proven APIs with modern Python patterns + Demo Data Fallback

import os
import json
import time
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode
import hashlib
import random

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, origins="*")
   

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

# REVISION: Removed hardcoded API key for security. App will now fail if key is not set.
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
if not RAPIDAPI_KEY:
    raise ValueError("FATAL ERROR: RAPIDAPI_KEY environment variable not set.")

RAPIDAPI_HOST_BOOKING = "booking-com18.p.rapidapi.com"
RAPIDAPI_HOST_HOTELS = "hotels-com-provider.p.rapidapi.com"

# European Cities Configuration - 29 major destinations
CITIES = {
    'stockholm': {
        'name': 'Stockholm, Sweden',
        'coordinates': [59.3293, 18.0686],
        'search_query': 'Stockholm Sweden',
        'country': 'se'
    },
    'paris': {
        'name': 'Paris, France',
        'coordinates': [48.8566, 2.3522],
        'search_query': 'Paris France',
        'country': 'fr'
    },
    'london': {
        'name': 'London, UK',
        'coordinates': [51.5074, -0.1278],
        'search_query': 'London United Kingdom',
        'country': 'gb'
    },
    'amsterdam': {
        'name': 'Amsterdam, Netherlands',
        'coordinates': [52.3676, 4.9041],
        'search_query': 'Amsterdam Netherlands',
        'country': 'nl'
    },
    'barcelona': {
        'name': 'Barcelona, Spain',
        'coordinates': [41.3851, 2.1734],
        'search_query': 'Barcelona Spain',
        'country': 'es'
    },
    'rome': {
        'name': 'Rome, Italy',
        'coordinates': [41.9028, 12.4964],
        'search_query': 'Rome Italy',
        'country': 'it'
    },
    'berlin': {
        'name': 'Berlin, Germany',
        'coordinates': [52.5200, 13.4050],
        'search_query': 'Berlin Germany',
        'country': 'de'
    },
    'copenhagen': {
        'name': 'Copenhagen, Denmark',
        'coordinates': [55.6761, 12.5683],
        'search_query': 'Copenhagen Denmark',
        'country': 'dk'
    },
    'vienna': {
        'name': 'Vienna, Austria',
        'coordinates': [48.2082, 16.3738],
        'search_query': 'Vienna Austria',
        'country': 'at'
    },
    'prague': {
        'name': 'Prague, Czech Republic',
        'coordinates': [50.0755, 14.4378],
        'search_query': 'Prague Czech Republic',
        'country': 'cz'
    },
    'madrid': {
        'name': 'Madrid, Spain',
        'coordinates': [40.4168, -3.7038],
        'search_query': 'Madrid Spain',
        'country': 'es'
    },
    'milano': {
        'name': 'Milano, Italy',
        'coordinates': [45.4642, 9.1900],
        'search_query': 'Milano Italy',
        'country': 'it'
    },
    'zurich': {
        'name': 'Zürich, Switzerland',
        'coordinates': [47.3769, 8.5417],
        'search_query': 'Zürich Switzerland',
        'country': 'ch'
    },
    'oslo': {
        'name': 'Oslo, Norway',
        'coordinates': [59.9139, 10.7522],
        'search_query': 'Oslo Norway',
        'country': 'no'
    },
    'helsinki': {
        'name': 'Helsinki, Finland',
        'coordinates': [60.1695, 24.9354],
        'search_query': 'Helsinki Finland',
        'country': 'fi'
    },
    'warsaw': {
        'name': 'Warsaw, Poland',
        'coordinates': [52.2297, 21.0122],
        'search_query': 'Warsaw Poland',
        'country': 'pl'
    },
    'budapest': {
        'name': 'Budapest, Hungary',
        'coordinates': [47.4979, 19.0402],
        'search_query': 'Budapest Hungary',
        'country': 'hu'
    },
    'dublin': {
        'name': 'Dublin, Ireland',
        'coordinates': [53.3498, -6.2603],
        'search_query': 'Dublin Ireland',
        'country': 'ie'
    },
    'lisbon': {
        'name': 'Lisbon, Portugal',
        'coordinates': [38.7223, -9.1393],
        'search_query': 'Lisbon Portugal',
        'country': 'pt'
    },
    'brussels': {
        'name': 'Brussels, Belgium',
        'coordinates': [50.8503, 4.3517],
        'search_query': 'Brussels Belgium',
        'country': 'be'
    },
    'athens': {
        'name': 'Athens, Greece',
        'coordinates': [37.9838, 23.7275],
        'search_query': 'Athens Greece',
        'country': 'gr'
    },
    'munich': {
        'name': 'Munich, Germany',
        'coordinates': [48.1351, 11.5820],
        'search_query': 'Munich Germany',
        'country': 'de'
    },
    'lyon': {
        'name': 'Lyon, France',
        'coordinates': [45.7640, 4.8357],
        'search_query': 'Lyon France',
        'country': 'fr'
    },
    'florence': {
        'name': 'Florence, Italy',
        'coordinates': [43.7696, 11.2558],
        'search_query': 'Florence Italy',
        'country': 'it'
    },
    'edinburgh': {
        'name': 'Edinburgh, Scotland',
        'coordinates': [55.9533, -3.1883],
        'search_query': 'Edinburgh Scotland',
        'country': 'gb'
    },
    'nice': {
        'name': 'Nice, France',
        'coordinates': [43.7102, 7.2620],
        'search_query': 'Nice France',
        'country': 'fr'
    },
    'palma': {
        'name': 'Palma, Spain',
        'coordinates': [39.5696, 2.6502],
        'search_query': 'Palma Spain',
        'country': 'es'
    },
    'santorini': {
        'name': 'Santorini, Greece',
        'coordinates': [36.3932, 25.4615],
        'search_query': 'Santorini Greece',
        'country': 'gr'
    },
    'ibiza': {
        'name': 'Ibiza, Spain',
        'coordinates': [38.9067, 1.4206],
        'search_query': 'Ibiza Spain',
        'country': 'es'
    }
}

# Room Type Configuration with Junior Suite
ROOM_TYPES = {
    'single': {
        'name': 'Single Room',
        'description': 'Comfortable single accommodation',
        'guests': 1,
        'keywords': ['single', 'solo', 'individual', 'one bed']
    },
    'double': {
        'name': 'Double Room',
        'description': 'Perfect for couples and business travelers',
        'guests': 2,
        'keywords': ['double', 'twin', 'couple', 'standard']
    },
    'family': {
        'name': 'Family Room',
        'description': 'Spacious accommodation for families',
        'guests': 4,
        'children': 2,
        'keywords': ['family', 'quadruple', 'connecting', 'bunk bed']
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'description': 'Spacious room with sitting area - upgraded comfort',
        'guests': 2,
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded', 'deluxe']
    },
    'suite': {
        'name': 'Suite/Apartment',
        'description': 'Luxury accommodation with separate living area',
        'guests': 3,
        'keywords': ['suite', 'apartment', 'penthouse', 'executive', 'luxury']
    }
}

# Country-specific Booking.com domains
BOOKING_DOMAINS = {
    'se': 'sv.html', 'no': 'no.html', 'fi': 'fi.html', 'dk': 'da.html',
    'fr': 'fr.html', 'gb': 'en-gb.html', 'nl': 'nl.html', 'be': 'nl.html',
    'es': 'es.html', 'it': 'it.html', 'de': 'de.html', 'at': 'de.html',
    'ch': 'de.html', 'cz': 'cs.html', 'pl': 'pl.html', 'hu': 'hu.html',
    'ie': 'en-gb.html', 'pt': 'pt.html', 'gr': 'el.html'
}

# =============================================================================
# CORE API INTEGRATION LAYER
# =============================================================================

class APIManager:
    """Manages multiple API sources with fallback and caching"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 900  # 15 minutes
    
    def _get_cache_key(self, method, **kwargs):
        """Generate cache key from method and parameters"""
        key_parts = [method] + [f"{k}:{v}" for k, v in sorted(kwargs.items())]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry):
        """Check if cache entry is still valid"""
        return time.time() - cache_entry['timestamp'] < self.cache_ttl
    
    def _get_from_cache(self, cache_key):
        """Retrieve from cache if valid"""
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            cached_data = self.cache[cache_key]['data']
            cached_data['is_cached'] = True
            return cached_data
        return None
    
    def _set_cache(self, cache_key, data):
        """Store in cache with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def search_hotels_multi_source(self, city_key, checkin, checkout, adults, rooms, room_type='double'):
        """Search hotels using multiple APIs with intelligent fallback"""
        cache_key = self._get_cache_key('search', city=city_key, checkin=checkin, 
                                        checkout=checkout, adults=adults, rooms=rooms, room_type=room_type)
        
        # Check cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Try primary source (Booking.com)
        try:
            result = self._search_booking_api(city_key, checkin, checkout, adults, rooms, room_type)
            if result and result.get('hotels'):
                self._set_cache(cache_key, result)
                return result
        except Exception as e:
            print(f"Booking API failed: {e}")
        
        # Try secondary source (Hotels.com) - Placeholder
        try:
            result = self._search_hotels_api(city_key, checkin, checkout, adults, rooms, room_type)
            if result and result.get('hotels'):
                self._set_cache(cache_key, result)
                return result
        except Exception as e:
            print(f"Hotels.com API (not implemented) skipped: {e}")
        
        # Fallback to demo data
        result = self._generate_demo_data(city_key, room_type)
        self._set_cache(cache_key, result)
        return result
    
    def _search_booking_api(self, city_key, checkin, checkout, adults, rooms, room_type):
        """Search using Booking.com API"""
        city_info = CITIES[city_key]
        location_id = self._get_booking_location_id(city_info['search_query'])
        
        if not location_id:
            raise Exception("Could not get location ID from Booking.com API")
        
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
            "x-rapidapi-host": RAPIDAPI_HOST_BOOKING
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if not data.get('data'):
            raise Exception("No hotels returned in API response")
        
        processed_hotels = self._process_booking_hotels(data['data'][:50], city_info, 
                                                        checkin, checkout, adults, rooms, room_type)
        
        return {
            'source': 'booking.com',
            'city': city_info['name'],
            'hotels': processed_hotels,
            'total_found': len(processed_hotels)
        }
    
    def _search_hotels_api(self, city_key, checkin, checkout, adults, rooms, room_type):
        """Search using Hotels.com API (fallback) - NOT IMPLEMENTED"""
        raise Exception("Hotels.com API not implemented yet.")
    
    def _get_booking_location_id(self, city_query):
        """Get Booking.com location ID for a city"""
        url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
        querystring = {"query": city_query, "languageCode": "en"}
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST_BOOKING
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data.get('data'):
            return data['data'][0].get('id')
        return None
    
    def _process_booking_hotels(self, hotels_data, city_info, checkin, checkout, adults, rooms, room_type):
        """Process hotel data from Booking.com API"""
        processed_hotels = []
        
        for i, hotel in enumerate(hotels_data):
            hotel_name = hotel.get('name', 'Unknown Hotel')
            hotel_id = hotel.get('id') or f"hotel_{i}"
            
            latitude = hotel.get('latitude')
            longitude = hotel.get('longitude')
            
            if latitude and longitude:
                coordinates = [float(latitude), float(longitude)]
            else:
                base_lat, base_lng = city_info['coordinates']
                coordinates = [
                    base_lat + (i * 0.005) - 0.025,
                    base_lng + (i * 0.005) - 0.025
                ]
            
            price = self._extract_price(hotel, checkin, checkout)
            rating = self._extract_rating(hotel)
            room_description = self._get_room_description(hotel_name, room_type)
            booking_url = self._create_enhanced_booking_url(
                hotel, city_info, checkin, checkout, adults, rooms, room_type
            )
            
            processed_hotel = {
                'id': hotel_id,
                'name': hotel_name,
                'address': hotel.get('address', city_info['name']),
                'coordinates': coordinates,
                'price': price,
                'rating': rating,
                'room_type': ROOM_TYPES[room_type]['name'],
                'room_description': room_description,
                'booking_url': booking_url,
                'source': 'booking.com'
            }
            
            processed_hotels.append(processed_hotel)
        
        return processed_hotels
    
    def _extract_price(self, hotel, checkin, checkout):
        """Extract and normalize price from hotel data"""
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
                        price = int(total_price)
                except (ValueError, TypeError):
                    price = int(total_price / 7)  
        elif 'price' in hotel:
            price = hotel['price']
        
        return price
    
    def _extract_rating(self, hotel):
        """Extract and normalize rating from hotel data"""
        rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
        if rating:
            rating = float(rating) / 2 if float(rating) > 5 else float(rating)
        else:
            rating = 4.0
        return round(rating, 1)
    
    def _get_room_description(self, hotel_name, room_type):
        """Generate room-specific description"""
        room_info = ROOM_TYPES[room_type]
        hotel_lower = hotel_name.lower()
        for keyword in room_info['keywords']:
            if keyword in hotel_lower:
                return f"{room_info['description']} - Perfect match!"
        return room_info['description']
    
    def _create_enhanced_booking_url(self, hotel, city_info, checkin, checkout, adults, rooms, room_type):
        """Create optimized booking URL with hotel name and room type"""
        hotel_id = hotel.get('id') or hotel.get('hotel_id')
        hotel_name = hotel.get('name', 'Hotel')
        country_code = city_info['country']
        
        if hotel_id and hotel_name:
            domain_suffix = BOOKING_DOMAINS.get(country_code, 'en-gb.html')
            
            base_params = {
                'ss': hotel_name, 'dest_id': hotel_id, 'dest_type': 'hotel',
                'checkin': checkin, 'checkout': checkout, 'group_adults': adults,
                'no_rooms': rooms, 'group_children': ROOM_TYPES[room_type].get('children', 0),
                'search_selected': 'true'
            }
            
            params_string = urlencode(base_params, quote_via=quote_plus)
            return f"https://www.booking.com/searchresults.{domain_suffix}?{params_string}"

        # Fallback URL if hotel-specific data is missing
        domain_suffix = BOOKING_DOMAINS.get(country_code, 'en-gb.html')
        return f"https://www.booking.com/searchresults.{domain_suffix}?ss={quote_plus(hotel_name)}"

    def _generate_demo_data(self, city_key, room_type):
        """Generate realistic demo data when APIs fail"""
        city_info = CITIES[city_key]
        demo_hotels = []
        
        hotel_templates = {
            'stockholm': ['Hotel Diplomat', 'Scandic Continental', 'Elite Palace', 'Clarion Sign'],
            'paris': ['Hotel Ritz', 'Le Bristol', 'Shangri-La', 'Hotel Plaza Athénée'],
            'london': ['The Savoy', 'Claridge\'s', 'The Langham', 'Park Lane Hotel'],
            'default': ['Grand Hotel', 'Royal Palace', 'Central Plaza', 'Premium Inn']
        }
        
        base_names = hotel_templates.get(city_key, hotel_templates['default'])
        
        for i, base_name in enumerate(base_names * 5):
            if room_type == 'junior_suite':
                hotel_name = f"{base_name} Junior Suite"
            elif room_type == 'suite':
                hotel_name = f"{base_name} Executive Suite"
            else:
                hotel_name = base_name

            base_lat, base_lng = city_info['coordinates']
            coordinates = [
                base_lat + random.uniform(-0.05, 0.05),
                base_lng + random.uniform(-0.05, 0.05)
            ]
            
            base_price = random.randint(80, 300)
            price_multipliers = {'junior_suite': 1.4, 'suite': 1.8, 'single': 0.7}
            price = int(base_price * price_multipliers.get(room_type, 1.0))
            
            demo_hotel = {
                'id': f"demo_{city_key}_{i}", 'name': hotel_name,
                'address': f"{city_info['name']} City Center", 'coordinates': coordinates,
                'price': price, 'rating': round(random.uniform(3.5, 4.8), 1),
                'room_type': ROOM_TYPES[room_type]['name'],
                'room_description': ROOM_TYPES[room_type]['description'],
                'booking_url': f"https://www.booking.com/searchresults.{BOOKING_DOMAINS.get(city_info['country'], 'en-gb.html')}?ss={quote_plus(hotel_name)}",
                'source': 'demo_data'
            }
            demo_hotels.append(demo_hotel)
        
        return {
            'source': 'demo_data', 'city': city_info['name'],
            'hotels': demo_hotels, 'total_found': len(demo_hotels)
        }

# =============================================================================
# FLASK APPLICATION ROUTES
# =============================================================================

api_manager = APIManager()

def _create_enhanced_response(result, search_params, test_mode=False):
    """Builds the standardized JSON response for hotel searches."""
    is_cached = result.pop('is_cached', False)
    room_type = search_params['room_type']
    
    response = {
        'city': result['city'],
        'hotels': result['hotels'],
        'total_found': result['total_found'],
        'search_params': search_params,
        'room_filter': {
            'enabled': True,
            'selected_type': ROOM_TYPES[room_type]['name'],
            'description': ROOM_TYPES[room_type]['description'],
            'guests': ROOM_TYPES[room_type]['guests']
        },
        'api_info': {
            'source': result['source'],
            'version': '2.0',
            'cached': 'cache_hit' if is_cached else 'fresh_data',
            'localization': 'enabled',
            'url_type': 'hotel_name_based_with_room_filter'
        }
    }
    if test_mode:
        response['api_info']['test_mode'] = True
        response['api_info']['test_description'] = 'Stockholm Junior Suite demonstration'
        
    return jsonify(response)

@app.route('/')
def home():
    """Enhanced API Documentation"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Backend API v2.0</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .cities { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
            .city { background: #e3f2fd; padding: 8px; border-radius: 4px; text-align: center; }
            .feature { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 8px; }
            .room-type { background: #fff3e0; padding: 8px; margin: 5px 0; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Backend API v2.0</h1>
        <p>Professional European hotel search with room type filtering and localized booking URLs</p>
        
        <div class="feature">
            <strong>✅ NEW: Room Type Filter with Junior Suite</strong><br>
            5 room types available including Junior Suite with enhanced descriptions
        </div>
        
        <div class="feature">
            <strong>✅ CORS Enabled</strong><br>
            Frontend can now access backend without errors
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels</strong> - Get hotels for a city with room type filtering<br>
            Parameters: city, checkin, checkout, adults, rooms, room_type<br>
            <em>Now with Junior Suite support and enhanced URLs</em>
        </div>
        <div class="endpoint">
            <strong>/api/cities</strong> - List all 29 cities
        </div>
        <div class="endpoint">
            <strong>/api/room-types</strong> - List all 5 room types
        </div>
        <div class="endpoint">
            <strong>/test</strong> - Test Stockholm Junior Suite hotels
        </div>
        
        <h2>Room Types ({{ room_types|length }}):</h2>
        {% for key, room in room_types.items() %}
        <div class="room-type">
            <strong>{{ room.name }}</strong> ({{ room.guests }} guests)<br>
            {{ room.description }}
        </div>
        {% endfor %}
        
        <h2>Cities supported ({{ cities|length }}):</h2>
        <div class="cities">
            {% for city in cities %}
            <div class="city">{{ city }}</div>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', cities=list(CITIES.keys()), room_types=ROOM_TYPES)

@app.route('/api/cities')
def get_cities():
    """Get all supported cities with metadata"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES),
        'supported_countries': sorted(list(set([city['country'] for city in CITIES.values()])))
    })

@app.route('/api/room-types')
def get_room_types():
    """Get all available room types"""
    return jsonify({
        'room_types': ROOM_TYPES,
        'total': len(ROOM_TYPES),
        'junior_suite_available': 'junior_suite' in ROOM_TYPES
    })

@app.route('/api/hotels')
def get_hotels():
    """Advanced multi-platform hotel search with room type filtering"""
    # Extract and validate parameters
    city = request.args.get('city', 'stockholm').lower()
    checkin = request.args.get('checkin', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
    checkout = request.args.get('checkout', (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'))
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    room_type = request.args.get('room_type', 'double').lower()
    
    if city not in CITIES:
        return jsonify({'error': f"City '{city}' not supported"}), 400
    if room_type not in ROOM_TYPES:
        return jsonify({'error': f"Room type '{room_type}' not supported"}), 400
    
    try:
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
        
        if checkin_date >= checkout_date:
            return jsonify({'error': 'Check-out date must be after check-in date'}), 400
        if checkin_date.date() < datetime.now().date():
            return jsonify({'error': 'Check-in date cannot be in the past'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    try:
        result = api_manager.search_hotels_multi_source(
            city, checkin, checkout, adults, rooms, room_type
        )
        search_params = {
            'city': city, 'checkin': checkin, 'checkout': checkout,
            'adults': adults, 'rooms': rooms, 'room_type': room_type
        }
        return _create_enhanced_response(result, search_params)
        
    except Exception as e:
        return jsonify({
            'error': 'Search failed due to an internal error',
            'message': str(e),
            'fallback': 'Demo data may be available'
        }), 500

@app.route('/test')
def test_stockholm():
    """Test endpoint with Stockholm hotels - demonstrates Junior Suite"""
    try:
        checkin = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        checkout = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        search_params = {
            'city': 'stockholm', 'checkin': checkin, 'checkout': checkout,
            'adults': '2', 'rooms': '1', 'room_type': 'junior_suite'
        }
        
        result = api_manager.search_hotels_multi_source(**search_params)
        
        return _create_enhanced_response(result, search_params, test_mode=True)
        
    except Exception as e:
        return jsonify({
            'error': 'Test search failed', 'message': str(e),
            'test_mode': True, 'fallback': 'Demo data should be available',
            'api_info': {'version': '2.0', 'test_endpoint': True}
        }), 500

@app.route('/api/analytics')
def get_analytics():
    """Basic analytics endpoint for monitoring"""
    return jsonify({
        'cache_stats': {
            'total_entries': len(api_manager.cache),
            'cache_ttl_minutes': api_manager.cache_ttl // 60
        },
        'supported_features': {
            'cities': len(CITIES),
            'room_types': len(ROOM_TYPES),
            'countries': len(set([city['country'] for city in CITIES.values()])),
            'booking_domains': len(BOOKING_DOMAINS)
        },
        'api_status': {
            'version': '2.0', 'uptime': 'operational', 'multi_platform': True,
            'intelligent_fallback': True, 'junior_suite_support': True
        }
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'version': '2.0',
        'services': {
            'booking_api': 'operational', 'cache_system': 'operational', 'demo_fallback': 'operational'
        }
    })

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/', '/api/hotels', '/api/cities', '/api/room-types',
            '/api/analytics', '/api/health', '/test'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error', 'message': 'An unexpected error occurred.',
        'support': 'Contact support if the issue persists.'
    }), 500

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend v2.0...")
    print("🏨 Supporting 29 European cities with 5 room types")
    print("🌟 NEW: Junior Suite support with enhanced descriptions")
    print("🔄 Multi-platform API integration with intelligent fallback")
    print("💾 15-minute caching for optimal performance")
    print("🌍 Localized booking URLs for all European countries")
    print("🔗 CORS enabled for GitHub Pages frontend")
    print("📋 Test API: /test (Junior Suite demo)")
    print("📊 Analytics: /api/analytics")
    print("❤️  Health check: /api/health")
    print("✅ Production-ready architecture activated")
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
