# STAYFINDR BACKEND - European Hotel Search Engine
# Flask backend with Booking.com + WORKING Hotels.com GraphQL integration
# BREAKTHROUGH: Using correct Hotels.com endpoints that actually work

import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import time
from datetime import datetime
from urllib.parse import quote_plus

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
        'search_query': 'Stockholm Sweden',
        'hotels_com_region_id': '178293'  # Stockholm region ID for Hotels.com
    },
    'paris': {
        'name': 'Paris, France', 
        'coordinates': [48.8566, 2.3522],
        'search_query': 'Paris France',
        'hotels_com_region_id': '179898'  # Paris region ID
    },
    'london': {
        'name': 'London, UK',
        'coordinates': [51.5074, -0.1278],
        'search_query': 'London United Kingdom',
        'hotels_com_region_id': '178279'  # London region ID
    },
    'amsterdam': {
        'name': 'Amsterdam, Netherlands',
        'coordinates': [52.3676, 4.9041],
        'search_query': 'Amsterdam Netherlands',
        'hotels_com_region_id': '179791'
    },
    'barcelona': {
        'name': 'Barcelona, Spain',
        'coordinates': [41.3851, 2.1734],
        'search_query': 'Barcelona Spain',
        'hotels_com_region_id': '179836'
    },
    'rome': {
        'name': 'Rome, Italy',
        'coordinates': [41.9028, 12.4964],
        'search_query': 'Rome Italy',
        'hotels_com_region_id': '179898'
    },
    'berlin': {
        'name': 'Berlin, Germany',
        'coordinates': [52.5200, 13.4050],
        'search_query': 'Berlin Germany',
        'hotels_com_region_id': '178276'
    },
    'copenhagen': {
        'name': 'Copenhagen, Denmark',
        'coordinates': [55.6761, 12.5683],
        'search_query': 'Copenhagen Denmark',
        'hotels_com_region_id': '179833'
    },
    'vienna': {
        'name': 'Vienna, Austria',
        'coordinates': [48.2082, 16.3738],
        'search_query': 'Vienna Austria',
        'hotels_com_region_id': '179842'
    },
    'prague': {
        'name': 'Prague, Czech Republic',
        'coordinates': [50.0755, 14.4378],
        'search_query': 'Prague Czech Republic',
        'hotels_com_region_id': '179895'
    },
    'madrid': {
        'name': 'Madrid, Spain',
        'coordinates': [40.4168, -3.7038],
        'search_query': 'Madrid Spain',
        'hotels_com_region_id': '179837'
    },
    'milano': {
        'name': 'Milano, Italy',
        'coordinates': [45.4642, 9.1900],
        'search_query': 'Milano Italy',
        'hotels_com_region_id': '179900'
    },
    'zurich': {
        'name': 'Zürich, Switzerland',
        'coordinates': [47.3769, 8.5417],
        'search_query': 'Zürich Switzerland',
        'hotels_com_region_id': '179841'
    },
    'oslo': {
        'name': 'Oslo, Norway',
        'coordinates': [59.9139, 10.7522],
        'search_query': 'Oslo Norway',
        'hotels_com_region_id': '179834'
    },
    'helsinki': {
        'name': 'Helsinki, Finland',
        'coordinates': [60.1695, 24.9354],
        'search_query': 'Helsinki Finland',
        'hotels_com_region_id': '179832'
    },
    'warsaw': {
        'name': 'Warsaw, Poland',
        'coordinates': [52.2297, 21.0122],
        'search_query': 'Warsaw Poland',
        'hotels_com_region_id': '179896'
    },
    'budapest': {
        'name': 'Budapest, Hungary',
        'coordinates': [47.4979, 19.0402],
        'search_query': 'Budapest Hungary',
        'hotels_com_region_id': '179835'
    },
    'dublin': {
        'name': 'Dublin, Ireland',
        'coordinates': [53.3498, -6.2603],
        'search_query': 'Dublin Ireland',
        'hotels_com_region_id': '179838'
    },
    'lisbon': {
        'name': 'Lisbon, Portugal',
        'coordinates': [38.7223, -9.1393],
        'search_query': 'Lisbon Portugal',
        'hotels_com_region_id': '179839'
    },
    'brussels': {
        'name': 'Brussels, Belgium',
        'coordinates': [50.8503, 4.3517],
        'search_query': 'Brussels Belgium',
        'hotels_com_region_id': '179840'
    },
    'athens': {
        'name': 'Athens, Greece',
        'coordinates': [37.9838, 23.7275],
        'search_query': 'Athens Greece',
        'hotels_com_region_id': '179843'
    },
    'munich': {
        'name': 'Munich, Germany',
        'coordinates': [48.1351, 11.5820],
        'search_query': 'Munich Germany',
        'hotels_com_region_id': '178277'
    },
    'lyon': {
        'name': 'Lyon, France',
        'coordinates': [45.7640, 4.8357],
        'search_query': 'Lyon France',
        'hotels_com_region_id': '179899'
    },
    'florence': {
        'name': 'Florence, Italy',
        'coordinates': [43.7696, 11.2558],
        'search_query': 'Florence Italy',
        'hotels_com_region_id': '179901'
    },
    'edinburgh': {
        'name': 'Edinburgh, Scotland',
        'coordinates': [55.9533, -3.1883],
        'search_query': 'Edinburgh Scotland',
        'hotels_com_region_id': '178280'
    },
    'nice': {
        'name': 'Nice, France',
        'coordinates': [43.7102, 7.2620],
        'search_query': 'Nice France',
        'hotels_com_region_id': '179902'
    },
    'palma': {
        'name': 'Palma, Spain',
        'coordinates': [39.5696, 2.6502],
        'search_query': 'Palma Spain',
        'hotels_com_region_id': '179844'
    },
    'santorini': {
        'name': 'Santorini, Greece',
        'coordinates': [36.3932, 25.4615],
        'search_query': 'Santorini Greece',
        'hotels_com_region_id': '179845'
    },
    'ibiza': {
        'name': 'Ibiza, Spain',
        'coordinates': [38.9067, 1.4206],
        'search_query': 'Ibiza Spain',
        'hotels_com_region_id': '179846'
    }
}

# Country codes for Booking.com URLs based on city
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

def get_location_id(city_query):
    """Get Booking.com location ID for a city"""
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {"query": city_query, "languageCode": "en"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_BOOKING
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return data['data'][0].get('id')
    except Exception as e:
        print(f"Error getting location ID: {e}")
    
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
        "x-rapidapi-host": RAPIDAPI_HOST_BOOKING
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error searching hotels: {e}")
    
    return None

def search_hotels_com_working(region_id, checkin, checkout, adults):
    """Search hotels using WORKING Hotels.com GraphQL endpoint"""
    
    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    
    # Convert date format from YYYY-MM-DD to proper format
    try:
        checkin_parts = checkin.split('-')
        checkout_parts = checkout.split('-')
        
        checkin_formatted = {
            "day": int(checkin_parts[2]),
            "month": int(checkin_parts[1]), 
            "year": int(checkin_parts[0])
        }
        
        checkout_formatted = {
            "day": int(checkout_parts[2]),
            "month": int(checkout_parts[1]),
            "year": int(checkout_parts[0])
        }
    except:
        # Fallback dates
        checkin_formatted = {"day": 15, "month": 7, "year": 2025}
        checkout_formatted = {"day": 16, "month": 7, "year": 2025}
    
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "destination": {"regionId": region_id},
        "checkInDate": checkin_formatted,
        "checkOutDate": checkout_formatted,
        "rooms": [{"adults": int(adults)}],
        "resultsStartingIndex": 0,
        "resultsSize": 25,
        "sort": "PRICE_LOW_TO_HIGH"
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_HOTELS
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Hotels.com API error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error in Hotels.com search: {e}")
    
    return None

def create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key):
    """Create hotel name-based booking URL for better targeting"""
    
    # Get hotel details
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('propertyId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id and hotel_name:
        # Get country code for the city
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        
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
    
    # Fallback URL
    hotel_name = hotel.get('name', '').replace(' ', '+')
    city_name = city_info['name'].replace(' ', '+')
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={hotel_name}+{city_name}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"

def create_hotels_com_url(hotel, checkin, checkout, adults):
    """Create Hotels.com booking URL"""
    
    # Get property ID
    property_id = hotel.get('id', 'unknown')
    
    # Build Hotels.com URL
    base_url = f"https://hotels.com/h{property_id}.Hotel-Information"
    params = f"?checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
    
    return base_url + params

def process_hotel_data_booking(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process and format Booking.com hotel data"""
    processed_hotels = []
    
    for i, hotel in enumerate(hotels_data):
        # Extract hotel information
        hotel_name = hotel.get('name', 'Unknown Hotel')
        
        # Get coordinates
        latitude = hotel.get('latitude')
        longitude = hotel.get('longitude')
        
        if latitude and longitude:
            coordinates = [float(latitude), float(longitude)]
        else:
            base_lat, base_lng = city_info['coordinates']
            coordinates = [
                base_lat + (i * 0.01) - 0.05,
                base_lng + (i * 0.01) - 0.05
            ]
        
        # Extract pricing
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
        elif 'price' in hotel:
            price = hotel['price']
        
        # Extract rating
        rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)
        else:
            rating = 4.0
        
        # Extract address
        address = hotel.get('address', city_info['name'])
        
        # Create booking URL
        booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key)
        
        processed_hotel = {
            'id': hotel.get('id') or f"booking_{i}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Booking.com',
            'booking_url': booking_url
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

def process_hotels_com_data(hotels_data, city_info, checkin, checkout, adults, rooms):
    """Process Hotels.com GraphQL data structure"""
    processed_hotels = []
    
    if not isinstance(hotels_data, dict) or 'data' not in hotels_data:
        return processed_hotels
    
    data = hotels_data.get('data', {})
    
    # Extract hotels from propertySearch -> properties
    properties = []
    if 'propertySearch' in data:
        property_search = data['propertySearch']
        if 'properties' in property_search:
            properties = property_search['properties']
    
    for i, hotel in enumerate(properties[:20]):  # Limit to 20
        if not isinstance(hotel, dict):
            continue
        
        # Hotel name
        hotel_name = hotel.get('name', f"Hotel {i+1}")
        
        # Coordinates
        coordinates = city_info.get('coordinates', [0.0, 0.0])
        try:
            if 'mapMarker' in hotel:
                map_marker = hotel['mapMarker']
                if 'latLong' in map_marker:
                    lat_long = map_marker['latLong']
                    lat = lat_long.get('latitude') or lat_long.get('lat')
                    lng = lat_long.get('longitude') or lat_long.get('lng')
                    if lat and lng:
                        coordinates = [float(lat), float(lng)]
        except (TypeError, ValueError, KeyError):
            pass
        
        # Price extraction
        price = 'N/A'
        try:
            if 'price' in hotel:
                price_data = hotel['price']
                if 'lead' in price_data:
                    lead_price = price_data['lead']
                    if 'amount' in lead_price:
                        price = int(lead_price['amount'])
        except (TypeError, ValueError, KeyError):
            pass
        
        # Rating
        rating = 4.0
        try:
            if 'reviews' in hotel:
                reviews = hotel['reviews']
                if 'score' in reviews:
                    score = reviews['score']
                    rating = float(score)
        except (TypeError, ValueError, KeyError):
            pass
        
        # Address
        address = city_info.get('name', 'Unknown Location')
        try:
            if 'neighborhood' in hotel:
                neighborhood = hotel['neighborhood']
                if 'name' in neighborhood:
                    address = neighborhood['name']
        except (TypeError, KeyError):
            pass
        
        # Booking URL
        booking_url = create_hotels_com_url(hotel, checkin, checkout, adults)
        
        processed_hotel = {
            'id': f"hotels_{hotel.get('id', i)}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Hotels.com',
            'booking_url': booking_url
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

@app.route('/')
def home():
    """API Documentation Page"""
    return jsonify({
        'name': 'STAYFINDR Backend - WORKING MULTIPLATFORM',
        'status': 'Online',
        'platforms': ['booking.com', 'hotels.com'],
        'cities': len(CITIES),
        'room_types': len(ROOM_TYPES),
        'message': 'European hotel search with WORKING Hotels.com GraphQL integration',
        'breakthrough': 'Hotels.com API now working with correct endpoints!'
    })

@app.route('/api/cities')
def get_cities():
    """Get all supported cities"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES)
    })

@app.route('/api/room-types')
def get_room_types():
    """Get all supported room types"""
    return jsonify({
        'room_types': ROOM_TYPES,
        'total': len(ROOM_TYPES)
    })

@app.route('/test-hotels-com-working')
def test_hotels_com_working():
    """Test WORKING Hotels.com GraphQL endpoint"""
    
    # Test Stockholm with correct region ID
    region_id = "178293"  # Stockholm region ID
    checkin = "2025-07-15"
    checkout = "2025-07-16"
    adults = 2
    
    hotels_data = search_hotels_com_working(region_id, checkin, checkout, adults)
    
    if hotels_data and 'data' in hotels_data:
        # Count properties
        property_count = 0
        if 'propertySearch' in hotels_data['data']:
            properties = hotels_data['data']['propertySearch'].get('properties', [])
            property_count = len(properties)
        
        # Get sample hotel
        sample_hotel = None
        if property_count > 0:
            sample_hotel = properties[0].get('name', 'Unknown')
        
        return jsonify({
            'status': 'SUCCESS! 🎉',
            'endpoint': 'properties/v2/list (WORKING GraphQL)',
            'city': 'Stockholm',
            'region_id': region_id,
            'hotels_found': property_count,
            'sample_hotel': sample_hotel,
            'api_response_keys': list(hotels_data.keys()),
            'message': 'Hotels.com API now working with correct GraphQL endpoint!'
        })
    else:
        return jsonify({
            'status': 'FAILED',
            'endpoint': 'properties/v2/list',
            'error': 'No data returned or API error',
            'response': hotels_data
        })

# Add this enhanced debug function to your backend

@app.route('/debug-hotels-com-detailed')
def debug_hotels_com_detailed():
    """Enhanced debug for Hotels.com API with full request/response logging"""
    
    debug_info = {
        'test_parameters': {
            'region_id': '178293',  # Stockholm
            'checkin': '2025-07-15',
            'checkout': '2025-07-16',
            'adults': 2
        },
        'api_details': {},
        'request_info': {},
        'response_analysis': {},
        'troubleshooting': {}
    }
    
    # Test parameters
    region_id = "178293"  # Stockholm
    checkin = "2025-07-15"
    checkout = "2025-07-16"
    adults = 2
    
    # Format dates
    try:
        checkin_parts = checkin.split('-')
        checkout_parts = checkout.split('-')
        
        checkin_formatted = {
            "day": int(checkin_parts[2]),
            "month": int(checkin_parts[1]), 
            "year": int(checkin_parts[0])
        }
        
        checkout_formatted = {
            "day": int(checkout_parts[2]),
            "month": int(checkout_parts[1]),
            "year": int(checkout_parts[0])
        }
        
        debug_info['request_info']['date_formatting'] = 'SUCCESS'
        debug_info['request_info']['checkin_formatted'] = checkin_formatted
        debug_info['request_info']['checkout_formatted'] = checkout_formatted
        
    except Exception as e:
        debug_info['request_info']['date_formatting'] = f'ERROR: {str(e)}'
        # Use fallback dates
        checkin_formatted = {"day": 15, "month": 7, "year": 2025}
        checkout_formatted = {"day": 16, "month": 7, "year": 2025}
    
    # Build request payload
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "destination": {"regionId": region_id},
        "checkInDate": checkin_formatted,
        "checkOutDate": checkout_formatted,
        "rooms": [{"adults": int(adults)}],
        "resultsStartingIndex": 0,
        "resultsSize": 25,
        "sort": "PRICE_LOW_TO_HIGH"
    }
    
    debug_info['request_info']['payload'] = payload
    debug_info['request_info']['payload_size'] = len(str(payload))
    
    # Headers
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_HOTELS
    }
    
    debug_info['api_details']['host'] = RAPIDAPI_HOST_HOTELS
    debug_info['api_details']['key_length'] = len(RAPIDAPI_KEY)
    debug_info['api_details']['key_starts_with'] = RAPIDAPI_KEY[:10] + "..."
    
    # Make request with detailed logging
    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    debug_info['request_info']['url'] = url
    debug_info['request_info']['method'] = 'POST'
    
    try:
        # Log request details
        debug_info['request_info']['headers_sent'] = {
            'content-type': headers['content-type'],
            'x-rapidapi-host': headers['x-rapidapi-host'],
            'x-rapidapi-key': f"{headers['x-rapidapi-key'][:10]}..."
        }
        
        # Make the actual request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Log response details
        debug_info['response_analysis']['status_code'] = response.status_code
        debug_info['response_analysis']['response_headers'] = dict(response.headers)
        debug_info['response_analysis']['response_size'] = len(response.text) if response.text else 0
        debug_info['response_analysis']['content_type'] = response.headers.get('content-type', 'unknown')
        
        # Check if we got any response
        if response.text:
            debug_info['response_analysis']['has_content'] = True
            debug_info['response_analysis']['first_100_chars'] = response.text[:100]
            
            # Try to parse JSON
            try:
                json_data = response.json()
                debug_info['response_analysis']['json_parse'] = 'SUCCESS'
                debug_info['response_analysis']['json_keys'] = list(json_data.keys()) if isinstance(json_data, dict) else 'NOT_DICT'
                
                # Analyze the structure
                if isinstance(json_data, dict):
                    if 'data' in json_data:
                        data = json_data['data']
                        debug_info['response_analysis']['has_data_key'] = True
                        debug_info['response_analysis']['data_type'] = type(data).__name__
                        
                        if isinstance(data, dict):
                            debug_info['response_analysis']['data_keys'] = list(data.keys())
                            
                            if 'propertySearch' in data:
                                prop_search = data['propertySearch']
                                debug_info['response_analysis']['has_property_search'] = True
                                debug_info['response_analysis']['property_search_keys'] = list(prop_search.keys()) if isinstance(prop_search, dict) else 'NOT_DICT'
                                
                                if isinstance(prop_search, dict) and 'properties' in prop_search:
                                    properties = prop_search['properties']
                                    debug_info['response_analysis']['properties_count'] = len(properties) if isinstance(properties, list) else 'NOT_LIST'
                                    debug_info['response_analysis']['properties_type'] = type(properties).__name__
                                    
                                    # Sample first property
                                    if isinstance(properties, list) and len(properties) > 0:
                                        first_prop = properties[0]
                                        debug_info['response_analysis']['sample_property_keys'] = list(first_prop.keys()) if isinstance(first_prop, dict) else 'NOT_DICT'
                                        debug_info['response_analysis']['sample_property_name'] = first_prop.get('name', 'NO_NAME') if isinstance(first_prop, dict) else 'CANNOT_ACCESS'
                            else:
                                debug_info['response_analysis']['property_search_missing'] = True
                        else:
                            debug_info['response_analysis']['data_not_dict'] = True
                    else:
                        debug_info['response_analysis']['no_data_key'] = True
                        debug_info['response_analysis']['available_keys'] = list(json_data.keys())
                
                # Include full response for small responses
                if len(str(json_data)) < 1000:
                    debug_info['response_analysis']['full_response'] = json_data
                    
            except json.JSONDecodeError as e:
                debug_info['response_analysis']['json_parse'] = f'FAILED: {str(e)}'
                debug_info['response_analysis']['raw_response'] = response.text[:500]
        else:
            debug_info['response_analysis']['has_content'] = False
            debug_info['response_analysis']['empty_response'] = True
            
    except requests.exceptions.Timeout:
        debug_info['response_analysis']['error'] = 'REQUEST_TIMEOUT'
    except requests.exceptions.ConnectionError:
        debug_info['response_analysis']['error'] = 'CONNECTION_ERROR'
    except Exception as e:
        debug_info['response_analysis']['error'] = f'EXCEPTION: {str(e)}'
    
    # Troubleshooting suggestions
    if debug_info['response_analysis'].get('status_code') == 200:
        debug_info['troubleshooting']['status'] = 'HTTP 200 OK - API accessible'
    elif debug_info['response_analysis'].get('status_code') == 403:
        debug_info['troubleshooting']['status'] = 'HTTP 403 - Check API subscription'
    elif debug_info['response_analysis'].get('status_code') == 429:
        debug_info['troubleshooting']['status'] = 'HTTP 429 - Rate limit exceeded'
    else:
        debug_info['troubleshooting']['status'] = f"HTTP {debug_info['response_analysis'].get('status_code', 'UNKNOWN')}"
    
    # Recommendations
    debug_info['troubleshooting']['recommendations'] = []
    
    if debug_info['response_analysis'].get('status_code') != 200:
        debug_info['troubleshooting']['recommendations'].append('Check API endpoint and subscription status')
    
    if not debug_info['response_analysis'].get('has_content'):
        debug_info['troubleshooting']['recommendations'].append('API returned empty response - check request format')
    
    if debug_info['response_analysis'].get('json_parse', '').startswith('FAILED'):
        debug_info['troubleshooting']['recommendations'].append('Response is not valid JSON - check API documentation')
    
    if not debug_info['response_analysis'].get('has_data_key'):
        debug_info['troubleshooting']['recommendations'].append('Response missing data key - API structure may have changed')
    
    return jsonify(debug_info)
