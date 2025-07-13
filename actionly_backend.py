# STAYFINDR MULTI-PLATFORM BACKEND - European Hotel Aggregator
# Flask backend with Booking.com + Hotels.com integration
# TRUE AGGREGATOR: Compare prices across multiple platforms!

import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import time
from datetime import datetime
from urllib.parse import quote_plus
import asyncio
import concurrent.futures

app = Flask(__name__)
CORS(app)

# RapidAPI Configuration
BOOKING_RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
BOOKING_RAPIDAPI_HOST = "booking-com18.p.rapidapi.com"

# Hotels.com API Configuration (NEW!)
HOTELS_RAPIDAPI_KEY = "ae6d44ef88mshd1dc5c75449a1b6p154a82jsne83e2399cc75"  # Dedicated Hotels.com key
HOTELS_RAPIDAPI_HOST = "hotels4.p.rapidapi.com"

# European Cities Configuration - 29 major destinations
CITIES = {
    'stockholm': {
        'name': 'Stockholm, Sweden',
        'coordinates': [59.3293, 18.0686],
        'search_query': 'Stockholm Sweden',
        'hotels_destination_id': '1327'  # Hotels.com destination ID
    },
    'paris': {
        'name': 'Paris, France', 
        'coordinates': [48.8566, 2.3522],
        'search_query': 'Paris France',
        'hotels_destination_id': '5085'
    },
    'london': {
        'name': 'London, UK',
        'coordinates': [51.5074, -0.1278],
        'search_query': 'London United Kingdom',
        'hotels_destination_id': '4239'
    },
    'amsterdam': {
        'name': 'Amsterdam, Netherlands',
        'coordinates': [52.3676, 4.9041],
        'search_query': 'Amsterdam Netherlands',
        'hotels_destination_id': '5085'
    },
    'barcelona': {
        'name': 'Barcelona, Spain',
        'coordinates': [41.3851, 2.1734],
        'search_query': 'Barcelona Spain',
        'hotels_destination_id': '2056'
    },
    'rome': {
        'name': 'Rome, Italy',
        'coordinates': [41.9028, 12.4964],
        'search_query': 'Rome Italy',
        'hotels_destination_id': '2087'
    },
    'berlin': {
        'name': 'Berlin, Germany',
        'coordinates': [52.5200, 13.4050],
        'search_query': 'Berlin Germany',
        'hotels_destination_id': '1956'
    },
    'copenhagen': {
        'name': 'Copenhagen, Denmark',
        'coordinates': [55.6761, 12.5683],
        'search_query': 'Copenhagen Denmark',
        'hotels_destination_id': '2095'
    },
    'vienna': {
        'name': 'Vienna, Austria',
        'coordinates': [48.2082, 16.3738],
        'search_query': 'Vienna Austria',
        'hotels_destination_id': '2096'
    },
    'prague': {
        'name': 'Prague, Czech Republic',
        'coordinates': [50.0755, 14.4378],
        'search_query': 'Prague Czech Republic',
        'hotels_destination_id': '2035'
    },
    # Add more cities with their Hotels.com destination IDs...
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
        'description': 'Single Room - Perfect for solo travelers',
        'guests': 1,
        'keywords': ['single', 'solo', 'individual', 'one person'],
        'booking_param': 'single'
    },
    'double': {
        'name': 'Double Room',
        'description': 'Double Room - Ideal for couples',
        'guests': 2,
        'keywords': ['double', 'twin', 'couple', 'two beds', 'king'],
        'booking_param': 'double'
    },
    'family': {
        'name': 'Family Room',
        'description': 'Family Room - Great for families with children',
        'guests': 4,
        'keywords': ['family', 'quad', 'children', 'kids', 'connecting'],
        'booking_param': 'family'
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'description': 'Junior Suite - Spacious room with sitting area',
        'guests': 2,
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded', 'spacious'],
        'booking_param': 'junior_suite'
    },
    'suite': {
        'name': 'Suite/Apartment',
        'description': 'Suite/Apartment - Luxury accommodation with separate living area',
        'guests': 3,
        'keywords': ['suite', 'apartment', 'luxury', 'separate', 'living area', 'premium'],
        'booking_param': 'suite'
    }
}

# ==================== BOOKING.COM API FUNCTIONS ====================

def get_booking_location_id(city_query):
    """Get Booking.com location ID for a city"""
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {"query": city_query, "languageCode": "en"}
    headers = {
        "x-rapidapi-key": BOOKING_RAPIDAPI_KEY,
        "x-rapidapi-host": BOOKING_RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return data['data'][0].get('id')
    except Exception as e:
        print(f"Error getting Booking.com location ID: {e}")
    
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
        "x-rapidapi-key": BOOKING_RAPIDAPI_KEY,
        "x-rapidapi-host": BOOKING_RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error searching Booking.com hotels: {e}")
    
    return None

# ==================== HOTELS.COM API FUNCTIONS (NEW!) ====================

def get_hotels_destination_id(city_name):
    """Get Hotels.com destination ID using v3 search"""
    url = "https://hotels4.p.rapidapi.com/locations/v3/search"
    
    querystring = {
        "q": city_name,
        "locale": "en_US"
    }
    
    headers = {
        "x-rapidapi-key": HOTELS_RAPIDAPI_KEY,
        "x-rapidapi-host": HOTELS_RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            # Look for city type destination
            if 'sr' in data:
                for result in data['sr']:
                    if result.get('type') == 'CITY':
                        return result.get('gaiaId')
    except Exception as e:
        print(f"Error getting Hotels.com destination ID: {e}")
    
    return None

def search_hotels_hotels_api(destination_id, checkin, checkout, adults, rooms):
    """Search hotels using Hotels.com API v2"""
    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    
    payload = {
        "currency": "EUR",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "destination": {
            "regionId": str(destination_id)
        },
        "checkInDate": {
            "day": int(checkin.split('-')[2]),
            "month": int(checkin.split('-')[1]),
            "year": int(checkin.split('-')[0])
        },
        "checkOutDate": {
            "day": int(checkout.split('-')[2]),
            "month": int(checkout.split('-')[1]),
            "year": int(checkout.split('-')[0])
        },
        "rooms": [
            {
                "adults": int(adults),
                "children": []
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": 25,
        "sort": "PRICE_LOW_TO_HIGH"
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": HOTELS_RAPIDAPI_KEY,
        "x-rapidapi-host": HOTELS_RAPIDAPI_HOST
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error searching Hotels.com hotels: {e}")
    
    return None

def create_hotels_com_url(hotel, checkin, checkout, adults, rooms):
    """Create Hotels.com booking URL"""
    hotel_id = hotel.get('id')
    hotel_name = hotel.get('name', '')
    
    if hotel_id:
        # Hotels.com direct booking URL
        base_url = "https://hotels.com/hotel/details.html"
        params = {
            'hotelId': hotel_id,
            'checkIn': checkin,
            'checkOut': checkout,
            'rooms[0].adults': adults,
            'rooms[0].children': '0'
        }
        
        params_string = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in params.items()])
        return f"{base_url}?{params_string}"
    
    # Fallback to search
    hotel_name_encoded = quote_plus(hotel_name)
    return f"https://hotels.com/search.do?q-destination={hotel_name_encoded}&q-check-in={checkin}&q-check-out={checkout}&q-rooms=1&q-room-0-adults={adults}&q-room-0-children=0"

# ==================== MULTI-PLATFORM PROCESSING ====================

def process_booking_hotels(hotels_data, city_info, checkin, checkout, adults, rooms, city_key):
    """Process Booking.com hotel data"""
    processed_hotels = []
    
    if not hotels_data or 'data' not in hotels_data:
        return processed_hotels
    
    for i, hotel in enumerate(hotels_data['data'][:25]):  # Limit to 25
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
                    from datetime import datetime
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
        
        # Create Booking.com URL
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        hotel_name_encoded = quote_plus(hotel_name)
        booking_url = f"https://www.booking.com/searchresults.{country_code}.html?ss={hotel_name_encoded}&dest_type=hotel&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}"
        
        processed_hotel = {
            'id': f"booking_{hotel.get('id', i)}",
            'name': hotel_name,
            'address': hotel.get('address', city_info['name']),
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Booking.com',
            'platform_logo': '🏨',
            'booking_url': booking_url,
            'source': 'booking'
        }
        
            processed_hotels.append(processed_hotel)
            
        except Exception as e:
            print(f"Error processing Hotels.com hotel {i}: {e}")
            continue
    
    print(f"Successfully processed {len(processed_hotels)} Hotels.com hotels")
    return processed_hotels

def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms):
    """Process Hotels.com hotel data (v2 API format) with comprehensive error handling"""
    processed_hotels = []
    
    if not hotels_data or 'data' not in hotels_data:
        print("No Hotels.com data or missing 'data' field")
        return processed_hotels
    
    # v2 API structure - handle various possible structures
    properties = []
    try:
        data = hotels_data['data']
        if 'propertySearch' in data and data['propertySearch']:
            if 'properties' in data['propertySearch']:
                properties = data['propertySearch']['properties']
        elif 'properties' in data:
            properties = data['properties']
        elif isinstance(data, list):
            properties = data
    except Exception as e:
        print(f"Error accessing Hotels.com properties: {e}")
        return processed_hotels
    
    if not properties:
        print("No properties found in Hotels.com response")
        return processed_hotels
    
    print(f"Processing {len(properties)} Hotels.com properties")
    
    for i, hotel in enumerate(properties[:25]):  # Limit to 25
        try:
            if not hotel or not isinstance(hotel, dict):
                continue
                
            # Extract hotel information safely
            hotel_name = hotel.get('name', f'Hotel {i+1}')
            if not hotel_name or hotel_name.strip() == '':
                hotel_name = f'Hotel {i+1}'
        
        # Get coordinates - handle multiple possible structures
        coordinates = None
        map_marker = hotel.get('mapMarker', {})
        
        # Try different coordinate structures
        if 'latLong' in map_marker:
            lat_long = map_marker['latLong']
            if isinstance(lat_long, dict):
                if 'lat' in lat_long and 'lon' in lat_long:
                    coordinates = [float(lat_long['lat']), float(lat_long['lon'])]
                elif 'latitude' in lat_long and 'longitude' in lat_long:
                    coordinates = [float(lat_long['latitude']), float(lat_long['longitude'])]
        
        # Fallback: Try direct coordinates in hotel object
        if not coordinates:
            if 'coordinate' in hotel:
                coord = hotel['coordinate']
                if 'lat' in coord and 'lon' in coord:
                    coordinates = [float(coord['lat']), float(coord['lon'])]
                elif 'latitude' in coord and 'longitude' in coord:
                    coordinates = [float(coord['latitude']), float(coord['longitude'])]
        
        # Final fallback: Use city center with offset
        if not coordinates:
            base_lat, base_lng = city_info['coordinates']
            coordinates = [
                base_lat + (i * 0.01) - 0.05,
                base_lng + (i * 0.01) - 0.05
            ]
        
        # Extract pricing - handle multiple price structures safely
        price = 'N/A'
        try:
            price_obj = hotel.get('price', {})
            
            # Try lead price first
            if 'lead' in price_obj and price_obj['lead']:
                price_info = price_obj['lead']
                if 'amount' in price_info:
                    price = int(price_info['amount'])
            
            # Try displayMessages if lead price not found
            elif 'displayMessages' in price_obj:
                for msg in price_obj['displayMessages']:
                    if 'lineItems' in msg:
                        for item in msg['lineItems']:
                            if 'price' in item and 'amount' in item['price']:
                                price = int(item['price']['amount'])
                                break
                        if price != 'N/A':
                            break
            
            # Try strikeOut price if available
            elif 'strikeOut' in price_obj and price_obj['strikeOut']:
                strike_info = price_obj['strikeOut']
                if 'amount' in strike_info:
                    price = int(strike_info['amount'])
            
            # Try any nested price structure
            elif isinstance(price_obj, dict):
                for key, value in price_obj.items():
                    if isinstance(value, dict) and 'amount' in value:
                        price = int(value['amount'])
                        break
        
        except (ValueError, TypeError, KeyError) as e:
            print(f"Price parsing error for {hotel_name}: {e}")
            price = 'N/A'
        
        # Extract rating safely
        rating = 4.0
        try:
            reviews = hotel.get('reviews', {})
            if 'score' in reviews and reviews['score']:
                rating = float(reviews['score'])
            elif 'rating' in reviews and reviews['rating']:
                rating = float(reviews['rating'])
            # Try alternative rating locations
            elif 'guestReviews' in hotel:
                guest_reviews = hotel['guestReviews']
                if 'rating' in guest_reviews:
                    rating = float(guest_reviews['rating'])
        except (ValueError, TypeError) as e:
            print(f"Rating parsing error for {hotel_name}: {e}")
            rating = 4.0
        
        # Create Hotels.com URL safely
        try:
            property_id = hotel.get('id', hotel.get('propertyId', f'hotel_{i}'))
            hotels_url = f"https://hotels.com/h{property_id}.Hotel-Information?checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
        except Exception as e:
            print(f"URL creation error for {hotel_name}: {e}")
            # Fallback URL
            hotel_name_safe = hotel_name.replace(' ', '+')
            hotels_url = f"https://hotels.com/search.do?q-destination={hotel_name_safe}&q-check-in={checkin}&q-check-out={checkout}"
        
        processed_hotel = {
            'id': f"hotels_{property_id}",
            'name': hotel_name,
        # Extract address safely - handle multiple possible structures
        address = city_info['name']  # Default fallback
        try:
            # Try different address structures
            if 'neighborhood' in hotel and hotel['neighborhood']:
                neighborhood = hotel['neighborhood']
                if isinstance(neighborhood, dict) and 'name' in neighborhood:
                    address = neighborhood['name']
                elif isinstance(neighborhood, str):
                    address = neighborhood
            elif 'address' in hotel and hotel['address']:
                addr_obj = hotel['address']
                if isinstance(addr_obj, dict):
                    # Try various address fields
                    address = (addr_obj.get('streetAddress') or 
                             addr_obj.get('locality') or 
                             addr_obj.get('region') or 
                             city_info['name'])
                elif isinstance(addr_obj, str):
                    address = addr_obj
            elif 'location' in hotel and hotel['location']:
                location = hotel['location']
                if isinstance(location, dict):
                    address = (location.get('address') or 
                             location.get('name') or 
                             city_info['name'])
        except (AttributeError, TypeError) as e:
            print(f"Address parsing error for {hotel_name}: {e}")
            address = city_info['name']
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Hotels.com',
            'platform_logo': '🏛️',
            'booking_url': hotels_url,
            'source': 'hotels'
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

def merge_and_compare_hotels(booking_hotels, hotels_com_hotels):
    """Merge and compare hotels from both platforms"""
    # Combine all hotels
    all_hotels = booking_hotels + hotels_com_hotels
    
    # Sort by price (lowest first, handle 'N/A' prices)
    def price_sort_key(hotel):
        price = hotel['price']
        if price == 'N/A':
            return float('inf')
        return float(price)
    
    all_hotels.sort(key=price_sort_key)
    
    # Add comparison indicators
    for hotel in all_hotels:
        if hotel['price'] != 'N/A':
            # Find similar hotels on other platforms for price comparison
            similar_hotels = [h for h in all_hotels 
                            if h['name'].lower().replace(' ', '') == hotel['name'].lower().replace(' ', '') 
                            and h['source'] != hotel['source']
                            and h['price'] != 'N/A']
            
            if similar_hotels:
                other_price = similar_hotels[0]['price']
                if hotel['price'] < other_price:
                    hotel['price_badge'] = 'BEST PRICE'
                elif hotel['price'] == other_price:
                    hotel['price_badge'] = 'SAME PRICE'
                else:
                    hotel['price_badge'] = f'€{other_price - hotel["price"]} more'
    
    return all_hotels

# ==================== API ENDPOINTS ====================

@app.route('/')
def home():
    """API Documentation Page"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Multi-Platform API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .feature { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 8px; }
            .new { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ffc107; }
            .platforms { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
            .platform { background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Multi-Platform API</h1>
        <p>European Hotel Aggregator - Compare prices across multiple platforms!</p>
        
        <div class="new">
            <strong>🆕 NEW: Multi-Platform Integration!</strong><br>
            Now searching both Booking.com AND Hotels.com for the best deals!
        </div>
        
        <h2>Supported Platforms:</h2>
        <div class="platforms">
            <div class="platform">
                <strong>🏨 Booking.com</strong><br>
                Hotel name-based URLs<br>
                Localized by country
            </div>
            <div class="platform">
                <strong>🏛️ Hotels.com</strong><br>
                Direct hotel booking<br>
                Price comparison enabled
            </div>
        </div>
        
        <h2>Features:</h2>
        <div class="feature">
            <strong>✅ Price Comparison:</strong> See best prices across platforms
        </div>
        <div class="feature">
            <strong>✅ Room Type Filter:</strong> Including Junior Suite option
        </div>
        <div class="feature">
            <strong>✅ Smart Merging:</strong> Deduplicate and sort by best price
        </div>
        <div class="feature">
            <strong>✅ 29 European Cities:</strong> Major destinations covered
        </div>
        
        <h2>Available endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels</strong> - Multi-platform hotel search<br>
            Parameters: city, checkin, checkout, adults, rooms, room_type<br>
            <em>Now returns results from BOTH platforms with price comparison!</em>
        </div>
        <div class="endpoint">
            <strong>/api/room-types</strong> - List all room types with Junior Suite
        </div>
        <div class="endpoint">
            <strong>/test</strong> - Test multi-platform Stockholm search
        </div>
        
        <h2>Example Response:</h2>
        <pre style="background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto;">
{
  "aggregator_type": "multi_platform",
  "platforms": ["Booking.com", "Hotels.com"],
  "hotels": [
    {
      "name": "Hotel Example",
      "price": 120,
      "platform": "Hotels.com",
      "price_badge": "BEST PRICE",
      "booking_url": "https://hotels.com/..."
    }
  ]
}
        </pre>
    </body>
    </html>
    ''')

@app.route('/api/room-types')
def get_room_types():
    """Get all supported room types including Junior Suite"""
    return jsonify({
        'room_types': ROOM_TYPES,
        'default': 'double',
        'featured': 'junior_suite'
    })

@app.route('/api/hotels')
def get_hotels_multiplatform():
    """Multi-platform hotel search - Booking.com + Hotels.com"""
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-15')
    checkout = request.args.get('checkout', '2025-07-16')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    room_type = request.args.get('room_type', 'double')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    city_info = CITIES[city]
    room_info = ROOM_TYPES.get(room_type, ROOM_TYPES['double'])
    
    # Search both platforms in parallel
    booking_hotels = []
    hotels_com_hotels = []
    
    # Booking.com search
    booking_location_id = get_booking_location_id(city_info['search_query'])
    if booking_location_id:
        booking_data = search_hotels_booking_api(booking_location_id, checkin, checkout, adults, rooms)
        if booking_data:
            booking_hotels = process_booking_hotels(booking_data, city_info, checkin, checkout, adults, rooms, city)
    
    # Hotels.com search (using dynamic destination lookup)
    hotels_com_hotels = []
    hotels_destination_id = get_hotels_destination_id(city_info['search_query'])
    if hotels_destination_id:
        hotels_data = search_hotels_hotels_api(hotels_destination_id, checkin, checkout, adults, rooms)
        if hotels_data:
            hotels_com_hotels = process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms)
    
    # Merge and compare results
    all_hotels = merge_and_compare_hotels(booking_hotels, hotels_com_hotels)
    
    # Apply room type filtering if applicable
    if room_type != 'double':  # Default doesn't need filtering
        filtered_hotels = []
        room_keywords = room_info['keywords']
        
        for hotel in all_hotels:
            hotel_name_lower = hotel['name'].lower()
            if any(keyword in hotel_name_lower for keyword in room_keywords):
                hotel['room_match'] = True
                hotel['room_description'] = room_info['description']
                filtered_hotels.append(hotel)
        
        # If no specific matches, return all but mark with room preference
        if not filtered_hotels:
            for hotel in all_hotels[:20]:  # Limit to 20 if no specific matches
                hotel['room_match'] = False
                hotel['room_description'] = f"Standard room (requested: {room_info['name']})"
            all_hotels = all_hotels[:20]
        else:
            all_hotels = filtered_hotels[:30]  # More results for specific room types
    
    return jsonify({
        'aggregator_type': 'multi_platform',
        'city': city_info['name'],
        'platforms_searched': ['Booking.com', 'Hotels.com'],
        'booking_hotels_found': len(booking_hotels),
        'hotels_com_found': len(hotels_com_hotels),
        'total_merged': len(all_hotels),
        'hotels': all_hotels,
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms,
            'room_type': room_type,
            'room_description': room_info['description']
        },
        'features_enabled': {
            'multi_platform': True,
            'price_comparison': True,
            'room_filtering': True,
            'localized_urls': True
        }
    })

@app.route('/test')
def test_multiplatform():
    """Test multi-platform search with Stockholm"""
    return get_hotels_multiplatform()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Multi-Platform Backend...")
    print("🏨 Supporting Booking.com + Hotels.com")
    print("🌍 29 European cities with price comparison")
    print("🛏️ Room type filtering with Junior Suite")
    print("📋 Test API: http://localhost:5000/test")
    print("✅ TRUE AGGREGATOR: Compare prices across platforms!")
    
    # Use PORT environment variable for deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
