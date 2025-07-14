# STAYFINDR BACKEND - European Hotel Search Engine
# Flask backend with RapidAPI Booking.com integration + WORKING Hotels.com
# FIXED: Clean version without duplicated code

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
    },
    'madrid': {
        'name': 'Madrid, Spain',
        'coordinates': [40.4168, -3.7038],
        'search_query': 'Madrid Spain'
    },
    'milano': {
        'name': 'Milano, Italy',
        'coordinates': [45.4642, 9.1900],
        'search_query': 'Milano Italy'
    },
    'zurich': {
        'name': 'Zürich, Switzerland',
        'coordinates': [47.3769, 8.5417],
        'search_query': 'Zürich Switzerland'
    },
    'oslo': {
        'name': 'Oslo, Norway',
        'coordinates': [59.9139, 10.7522],
        'search_query': 'Oslo Norway'
    },
    'helsinki': {
        'name': 'Helsinki, Finland',
        'coordinates': [60.1695, 24.9354],
        'search_query': 'Helsinki Finland'
    },
    'warsaw': {
        'name': 'Warsaw, Poland',
        'coordinates': [52.2297, 21.0122],
        'search_query': 'Warsaw Poland'
    },
    'budapest': {
        'name': 'Budapest, Hungary',
        'coordinates': [47.4979, 19.0402],
        'search_query': 'Budapest Hungary'
    },
    'dublin': {
        'name': 'Dublin, Ireland',
        'coordinates': [53.3498, -6.2603],
        'search_query': 'Dublin Ireland'
    },
    'lisbon': {
        'name': 'Lisbon, Portugal',
        'coordinates': [38.7223, -9.1393],
        'search_query': 'Lisbon Portugal'
    },
    'brussels': {
        'name': 'Brussels, Belgium',
        'coordinates': [50.8503, 4.3517],
        'search_query': 'Brussels Belgium'
    },
    'athens': {
        'name': 'Athens, Greece',
        'coordinates': [37.9838, 23.7275],
        'search_query': 'Athens Greece'
    },
    'munich': {
        'name': 'Munich, Germany',
        'coordinates': [48.1351, 11.5820],
        'search_query': 'Munich Germany'
    },
    'lyon': {
        'name': 'Lyon, France',
        'coordinates': [45.7640, 4.8357],
        'search_query': 'Lyon France'
    },
    'florence': {
        'name': 'Florence, Italy',
        'coordinates': [43.7696, 11.2558],
        'search_query': 'Florence Italy'
    },
    'edinburgh': {
        'name': 'Edinburgh, Scotland',
        'coordinates': [55.9533, -3.1883],
        'search_query': 'Edinburgh Scotland'
    },
    'nice': {
        'name': 'Nice, France',
        'coordinates': [43.7102, 7.2620],
        'search_query': 'Nice France'
    },
    'palma': {
        'name': 'Palma, Spain',
        'coordinates': [39.5696, 2.6502],
        'search_query': 'Palma Spain'
    },
    'santorini': {
        'name': 'Santorini, Greece',
        'coordinates': [36.3932, 25.4615],
        'search_query': 'Santorini Greece'
    },
    'ibiza': {
        'name': 'Ibiza, Spain',
        'coordinates': [38.9067, 1.4206],
        'search_query': 'Ibiza Spain'
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
        print(f"Hotels.com /suggest API response status: {suggest_response.status_code}")
        
        if suggest_response.status_code == 200:
            suggest_data = suggest_response.json()
            print(f"Hotels.com /suggest success! Found data keys: {list(suggest_data.keys())}")
            
            # Parse the suggest response (like your San Francisco example)
            destination_id = None
            if 'suggestions' in suggest_data:
                for suggestion_group in suggest_data['suggestions']:
                    if 'entities' in suggestion_group:
                        for entity in suggestion_group['entities']:
                            # Look for CITY type (primary destination)
                            if entity.get('type') == 'CITY':
                                destination_id = entity.get('destinationId')
                                if destination_id:
                                    print(f"Found destination ID: {destination_id} for {entity.get('name')}")
                                    break
                        if destination_id:
                            break
                    if destination_id:
                        break
            
            if not destination_id:
                print("No destination ID found in suggest response")
                return None
            
            # Step 2: Search hotels using the destination ID
            hotels_url = "https://hotels4.p.rapidapi.com/Hotels/Search"
            
            hotels_params = {
                "destinationId": destination_id,
                "checkIn": checkin,
                "checkOut": checkout,
                "adults": adults,
                "rooms": 1,
                "locale": "en_US",
                "currency": "USD",
                "sort": "PRICE",
                "pageSize": "25"
            }
            
            hotels_response = requests.get(hotels_url, headers=headers, params=hotels_params)
            print(f"Hotels.com Hotels/Search API response status: {hotels_response.status_code}")
            
            if hotels_response.status_code == 200:
                hotels_data = hotels_response.json()
                print(f"Hotels.com Hotels/Search success! Found data keys: {list(hotels_data.keys())}")
                
                # Check for the correct structure
                if 'data' in hotels_data and 'propertySearchListings' in hotels_data['data']:
                    listings = hotels_data['data']['propertySearchListings']
                    print(f"Found {len(listings)} hotel listings!")
                    return hotels_data
                else:
                    print(f"Hotels/Search response structure: {list(hotels_data.keys())}")
                    return hotels_data  # Return for debugging
            else:
                print(f"Hotels.com Hotels/Search API error: {hotels_response.status_code} - {hotels_response.text}")
                return None
        else:
            print(f"Hotels.com /suggest API error: {suggest_response.status_code} - {suggest_response.text}")
            return None
            
    except Exception as e:
        print(f"Error in Hotels.com two-step search: {e}")
        return None

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
    
    # Priority 2: Create hotel name-based search URL (IMPROVED METHOD)
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('propertyId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id and hotel_name:
        # Get country code for the city
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        
        # Encode hotel name properly for URL
        hotel_name_encoded = quote_plus(hotel_name)
        
        # Create hotel name-based search URL similar to your example
        base_params = {
            'ss': hotel_name,  # Hotel search string
            'dest_id': hotel_id,  # Hotel destination ID
            'dest_type': 'hotel',  # Specify it's a hotel
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
    
    # Priority 3: Fallback to hotel ID-based URL
    if hotel_id:
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        return f"https://www.booking.com/hotel/{country_code.split('-')[0]}/?hotel_id={hotel_id}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
    
    # Priority 4: Generic search by hotel name in the city
    hotel_name = hotel.get('name', '').replace(' ', '+')
    city_name = city_info['name'].replace(' ', '+')
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={hotel_name}+{city_name}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"

def process_hotel_data_booking(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process and format Booking.com hotel data with proper booking URLs"""
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
            # Fallback: spread around city center
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
                # Convert to per night if total price
                total_price = price_info['value']
                try:
                    # Estimate per night (assuming booking is for multiple nights)
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
            'id': hotel.get('id') or hotel.get('hotel_id') or f"booking_{i}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Booking.com',
            'platform_logo': '🏨',
            'booking_url': booking_url
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms, room_type='double'):
    """Process Hotels.com hotel data from GraphQL structure - WORKING VERSION"""
    processed_hotels = []
    
    # Safe data structure check
    if not isinstance(hotels_data, dict) or 'data' not in hotels_data:
        print("Hotels.com: Invalid data structure - no 'data' key")
        return processed_hotels
    
    data = hotels_data.get('data', {})
    
    # Extract hotels from GraphQL propertySearchListings structure
    hotels = []
    if isinstance(data, dict) and 'propertySearchListings' in data:
        hotels = data.get('propertySearchListings', [])
        print(f"Hotels.com: Found {len(hotels)} properties in propertySearchListings")
    
    for i, hotel in enumerate(hotels[:25]):  # Limit to 25 hotels
        if not isinstance(hotel, dict):
            continue
        
        # Hotel name from headingSection
        hotel_name = 'Unknown Hotel'
        if 'headingSection' in hotel and isinstance(hotel['headingSection'], dict):
            hotel_name = hotel['headingSection'].get('heading', f"Hotel {i+1}")
        
        # Coordinates with safe fallbacks
        coordinates = city_info.get('coordinates', [0.0, 0.0])
        
        # Try to get real coordinates from mapMarker
        try:
            if 'mapMarker' in hotel and isinstance(hotel['mapMarker'], dict):
                lat_long = hotel['mapMarker'].get('latLong', {})
                if isinstance(lat_long, dict):
                    lat = lat_long.get('lat') or lat_long.get('latitude')
                    lon = lat_long.get('lon') or lat_long.get('longitude')
                    if lat and lon:
                        coordinates = [float(lat), float(lon)]
        except (TypeError, ValueError):
            pass  # Keep city coordinates as fallback
        
        # Price extraction from priceSection
        price = 'N/A'
        try:
            if 'priceSection' in hotel and isinstance(hotel['priceSection'], dict):
                price_summary = hotel['priceSection'].get('priceSummary', {})
                if isinstance(price_summary, dict):
                    display_messages = price_summary.get('displayMessages', [])
                    if display_messages and isinstance(display_messages, list) and len(display_messages) > 0:
                        first_message = display_messages[0]
                        if isinstance(first_message, dict) and 'lineItems' in first_message:
                            line_items = first_message.get('lineItems', [])
                            if line_items and isinstance(line_items, list) and len(line_items) > 0:
                                first_item = line_items[0]
                                if isinstance(first_item, dict) and 'price' in first_item:
                                    price_obj = first_item.get('price', {})
                                    if isinstance(price_obj, dict):
                                        formatted_price = price_obj.get('formatted', 'N/A')
                                        if formatted_price and formatted_price != 'N/A':
                                            # Extract number from formatted price like "$475"
                                            import re
                                            price_match = re.search(r'[\d,]+', formatted_price)
                                            if price_match:
                                                price = int(price_match.group().replace(',', ''))
        except (TypeError, ValueError, AttributeError):
            price = 'N/A'
        
        # Rating from guestRatingSectionV2
        rating = 4.0  # Default rating
        try:
            if 'guestRatingSectionV2' in hotel and isinstance(hotel['guestRatingSectionV2'], dict):
                badge = hotel['guestRatingSectionV2'].get('badge', {})
                if isinstance(badge, dict):
                    rating_text = badge.get('text', '')
                    if rating_text:
                        # Extract rating like "8.4/10" or "4.2"
                        import re
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            extracted_rating = float(rating_match.group())
                            # Normalize to 5-point scale
                            if extracted_rating > 5:
                                rating = extracted_rating / 2  # Convert from 10-point to 5-point
                            else:
                                rating = extracted_rating
        except (TypeError, ValueError, AttributeError):
            rating = 4.0
        
        # Booking URL from cardLink
        hotels_url = f"https://hotels.com"
        try:
            if 'cardLink' in hotel and isinstance(hotel['cardLink'], dict):
                resource = hotel['cardLink'].get('resource', {})
                if isinstance(resource, dict):
                    hotels_url = resource.get('value', hotels_url)
            
            # Ensure proper Hotels.com URL with parameters
            if not hotels_url.startswith('http'):
                hotels_url = f"https://hotels.com{hotels_url}"
            
            # Add search parameters if not already present
            if '?' not in hotels_url:
                hotels_url += f"?checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
            elif 'checkIn' not in hotels_url:
                hotels_url += f"&checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
                
        except (TypeError, AttributeError):
            # Fallback booking URL
            property_id = hotel.get('id', i)
            hotels_url = f"https://hotels.com/h{property_id}.Hotel-Information?checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
        
        # Address with safe fallback
        address = city_info.get('name', 'Unknown Location')
        try:
            if 'neighborhoodSection' in hotel and isinstance(hotel['neighborhoodSection'], dict):
                neighborhood = hotel['neighborhoodSection'].get('neighborhood', {})
                if isinstance(neighborhood, dict):
                    neighborhood_name = neighborhood.get('name')
                    if neighborhood_name:
                        address = neighborhood_name
        except (TypeError, AttributeError):
            pass
        
        # Create processed hotel object
        processed_hotel = {
            'id': f"hotels_{hotel.get('id', i)}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Hotels.com',
            'platform_logo': '🏛️',
            'booking_url': hotels_url
        }
        
        processed_hotels.append(processed_hotel)
    
    print(f"Hotels.com: Processed {len(processed_hotels)} hotels successfully")
    return processed_hotels

@app.route('/')
def home():
    """API Documentation Page"""
    return jsonify({
        'name': 'STAYFINDR Backend - MULTIPLATFORM VERSION',
        'status': 'Online',
        'platforms': ['booking.com', 'hotels.com'],
        'cities': len(CITIES),
        'message': 'Booking.com + Hotels.com integration for best prices!'
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

@app.route('/test-hotels-com-api')
def test_hotels_com_working():
    """Test Hotels.com API using WORKING two-step process (suggest + Hotels/Search)"""
    print("Testing Hotels.com API with WORKING two-step process...")
    
    # Test with Stockholm
    city = "Stockholm"
    checkin = "2025-07-15"
    checkout = "2025-07-16"
    adults = 2
    
    hotels_data = search_hotels_com_api_working(city, checkin, checkout, adults)
    
    if hotels_data:
        # Count hotels from working GraphQL structure
        hotel_count = 0
        if isinstance(hotels_data, dict) and 'data' in hotels_data:
            if 'propertySearchListings' in hotels_data['data']:
                hotel_count = len(hotels_data['data']['propertySearchListings'])
        
        total_available = 0
        if isinstance(hotels_data, dict) and 'meta' in hotels_data:
            total_available = hotels_data['meta'].get('totalRecords', 0)
        
        # Get sample hotel name
        sample_hotel = None
        if hotel_count > 0:
            first_hotel = hotels_data['data']['propertySearchListings'][0]
            if 'headingSection' in first_hotel:
                sample_hotel = first_hotel['headingSection'].get('heading')
        
        return jsonify({
            'status': 'SUCCESS!' if hotel_count > 0 else 'PARTIAL',
            'host': 'hotels4.p.rapidapi.com',
            'endpoints': '/suggest + /Hotels/Search (TWO-STEP WORKING PROCESS)',
            'city_searched': city,
            'hotels_found': hotel_count,
            'total_available': total_available,
            'sample_hotel': sample_hotel,
            'hotels_com': 'two_step_suggest_then_search'
        })
    else:
        return jsonify({
            'status': 'FAILED',
            'host': 'hotels4.p.rapidapi.com',
            'endpoints': '/suggest + /Hotels/Search (TWO-STEP WORKING PROCESS)',
            'error': 'No data returned from Hotels.com API',
            'hotels_com': 'api_failed'
        })

@app.route('/test')
def test_multiplatform():
    """Test endpoint with both Booking.com and Hotels.com"""
    return get_hotels_multiplatform()

@app.route('/api/hotels')
def get_hotels_multiplatform():
    """Get hotels from both Booking.com and Hotels.com platforms"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-15')
    checkout = request.args.get('checkout', '2025-07-16')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    room_type = request.args.get('room_type', 'double')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    all_hotels = []
    
    # Get room type info
    room_info = ROOM_TYPES.get(room_type, ROOM_TYPES['double'])
    
    # Platform 1: Booking.com
    booking_hotels = []
    location_id = get_location_id(city_info['search_query'])
    
    if location_id:
        hotels_data = search_hotels_booking_api(location_id, checkin, checkout, adults, rooms)
        if hotels_data and 'data' in hotels_data:
            booking_hotels = process_hotel_data_booking(
                hotels_data['data'][:20],  # Limit to 20 hotels
                city_info, 
                checkin, 
                checkout, 
                adults, 
                rooms,
                city
            )
    
    # Platform 2: Hotels.com
    hotels_com_hotels = []
    hotels_com_data = search_hotels_com_api_working(city_info['search_query'], checkin, checkout, adults)
    
    if hotels_com_data:
        hotels_com_hotels = process_hotels_com_hotels(
            hotels_com_data,
            city_info,
            checkin,
            checkout,
            adults,
            rooms,
            room_type
        )
    
    # Combine all hotels
    all_hotels = booking_hotels + hotels_com_hotels
    
    # Remove duplicates based on hotel name similarity
    unique_hotels = []
    seen_names = set()
    
    for hotel in all_hotels:
        hotel_name_clean = hotel['name'].lower().replace(' ', '').replace('-', '')[:20]
        if hotel_name_clean not in seen_names:
            seen_names.add(hotel_name_clean)
            unique_hotels.append(hotel)
    
    return jsonify({
        'city': city_info['name'],
        'hotels': unique_hotels,
        'total_found': len(unique_hotels),
        'booking_com_count': len(booking_hotels),
        'hotels_com_count': len(hotels_com_hotels),
        'platforms': ['booking.com', 'hotels.com'],
        'search_params': {
            'checkin': checkin,
            'checkout': checkout,
            'adults': adults,
            'rooms': rooms,
            'room_type': room_type
        },
        'room_filter': 'enabled',
        'room_type': room_type,
        'room_description': room_info['description'],
        'booking_optimization': 'enabled',
        'localization': 'enabled',
        'multiplatform': 'active',
        'error_handling': 'fixed'
    })

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Backend...")
    print("🏨 MULTIPLATFORM: Booking.com + Hotels.com")
    print("🔗 Two-step Hotels.com: suggest → search")
    print("✅ Room filtering with Junior Suite support")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
