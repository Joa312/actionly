# ACTIONLY FLASK BACKEND - Real Hotel Data for 29 European Cities
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
import json
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# Your working RapidAPI key
RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"

# 29 European cities with their location IDs (we'll populate these)
CITIES = {
    'stockholm': {
        'name': 'Stockholm, Sweden',
        'location_id': 'eyJjaXR5X25hbWUiOiJTdG9ja2hvbG0iLCJjb3VudHJ5IjoiU3dlZGVuIiwiZGVzdF9pZCI6Ii0yNTI0Mjc5IiwiZGVzdF90eXBlIjoiY2l0eSJ9',
        'coordinates': [59.3293, 18.0686]
    },
    'paris': {
        'name': 'Paris, France', 
        'location_id': None,  # Will be populated
        'coordinates': [48.8566, 2.3522]
    },
    'london': {
        'name': 'London, UK',
        'location_id': None,
        'coordinates': [51.5074, -0.1278]
    },
    'amsterdam': {
        'name': 'Amsterdam, Netherlands',
        'location_id': None,
        'coordinates': [52.3676, 4.9041]
    },
    'barcelona': {
        'name': 'Barcelona, Spain',
        'location_id': None,
        'coordinates': [41.3851, 2.1734]
    },
    'rome': {
        'name': 'Rome, Italy',
        'location_id': None,
        'coordinates': [41.9028, 12.4964]
    },
    'berlin': {
        'name': 'Berlin, Germany',
        'location_id': None,
        'coordinates': [52.5200, 13.4050]
    },
    'copenhagen': {
        'name': 'Copenhagen, Denmark',
        'location_id': None,
        'coordinates': [55.6761, 12.5683]
    },
    'vienna': {
        'name': 'Vienna, Austria',
        'location_id': None,
        'coordinates': [48.2082, 16.3738]
    },
    'prague': {
        'name': 'Prague, Czech Republic',
        'location_id': None,
        'coordinates': [50.0755, 14.4378]
    },
    'madrid': {
        'name': 'Madrid, Spain',
        'location_id': None,
        'coordinates': [40.4168, -3.7038]
    },
    'milano': {
        'name': 'Milano, Italy',
        'location_id': None,
        'coordinates': [45.4642, 9.1900]
    },
    'zurich': {
        'name': 'Zürich, Switzerland',
        'location_id': None,
        'coordinates': [47.3769, 8.5417]
    },
    'oslo': {
        'name': 'Oslo, Norway',
        'location_id': None,
        'coordinates': [59.9139, 10.7522]
    },
    'helsinki': {
        'name': 'Helsinki, Finland',
        'location_id': None,
        'coordinates': [60.1699, 24.9384]
    },
    'warsaw': {
        'name': 'Warsaw, Poland',
        'location_id': None,
        'coordinates': [52.2297, 21.0122]
    },
    'budapest': {
        'name': 'Budapest, Hungary',
        'location_id': None,
        'coordinates': [47.4979, 19.0402]
    },
    'dublin': {
        'name': 'Dublin, Ireland',
        'location_id': None,
        'coordinates': [53.3498, -6.2603]
    },
    'lisbon': {
        'name': 'Lisbon, Portugal',
        'location_id': None,
        'coordinates': [38.7223, -9.1393]
    },
    'brussels': {
        'name': 'Brussels, Belgium',
        'location_id': None,
        'coordinates': [50.8503, 4.3517]
    },
    'athens': {
        'name': 'Athens, Greece',
        'location_id': None,
        'coordinates': [37.9838, 23.7275]
    },
    'munich': {
        'name': 'Munich, Germany',
        'location_id': None,
        'coordinates': [48.1351, 11.5820]
    },
    'lyon': {
        'name': 'Lyon, France',
        'location_id': None,
        'coordinates': [45.7640, 4.8357]
    },
    'florence': {
        'name': 'Florence, Italy',
        'location_id': None,
        'coordinates': [43.7696, 11.2558]
    },
    'edinburgh': {
        'name': 'Edinburgh, Scotland',
        'location_id': None,
        'coordinates': [55.9533, -3.1883]
    },
    'nice': {
        'name': 'Nice, France',
        'location_id': None,
        'coordinates': [43.7102, 7.2620]
    },
    'palma': {
        'name': 'Palma, Spain',
        'location_id': None,
        'coordinates': [39.5696, 2.6502]
    },
    'santorini': {
        'name': 'Santorini, Greece',
        'location_id': None,
        'coordinates': [36.3932, 25.4615]
    },
    'ibiza': {
        'name': 'Ibiza, Spain',
        'location_id': None,
        'coordinates': [38.9067, 1.4206]
    }
}

def find_city_location_id(city_name):
    """Find location ID for a city using RapidAPI autocomplete"""
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {
        "query": city_name,
        "languageCode": "en"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "booking-com18.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return data['data'][0]['id']
    except Exception as e:
        print(f"Error finding location for {city_name}: {e}")
    
    return None

def get_hotels_for_city(city_key, checkin_date, checkout_date, adults=2, rooms=1):
    """Get real hotel data for a city"""
    
    if city_key not in CITIES:
        return {'error': f'City {city_key} not found'}
    
    city_info = CITIES[city_key]
    location_id = city_info['location_id']
    
    # If we don't have location_id, try to find it
    if not location_id:
        print(f"Finding location ID for {city_info['name']}...")
        location_id = find_city_location_id(city_info['name'])
        if location_id:
            CITIES[city_key]['location_id'] = location_id
        else:
            return {'error': f'Could not find location ID for {city_info["name"]}'}
    
    # Get hotels from Booking.com
    url = "https://booking-com18.p.rapidapi.com/stays/search"
    
    querystring = {
        "locationId": location_id,
        "checkinDate": checkin_date,
        "checkoutDate": checkout_date,
        "adults": str(adults),
        "rooms": str(rooms),
        "currency": "EUR"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "booking-com18.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            data = response.json()
            hotels_data = data.get('data', [])
            
            # Convert to ACTIONLY format - GET ALL HOTELS
            hotels = []
            for i, hotel in enumerate(hotels_data):  # Get ALL hotels from API (all 21!)
                
                # Extract price information
                price = 'N/A'
                if 'priceBreakdown' in hotel:
                    price_info = hotel['priceBreakdown'].get('grossPrice', {})
                    if 'value' in price_info:
                        total_price = price_info['value']
                        # Calculate per night (assuming 7 nights default)
                        try:
                            from datetime import datetime
                            checkin = datetime.strptime(checkin_date, '%Y-%m-%d')
                            checkout = datetime.strptime(checkout_date, '%Y-%m-%d')
                            nights = (checkout - checkin).days
                            if nights > 0:
                                price = round(total_price / nights)
                            else:
                                price = total_price
                        except:
                            price = total_price
                
                # Extract real coordinates from API
                latitude = hotel.get('latitude')
                longitude = hotel.get('longitude')
                
                # Use real coordinates if available, otherwise fallback to city center with small offset
                if latitude and longitude:
                    coordinates = [float(latitude), float(longitude)]
                else:
                    # Fallback with small random offset
                    import random
                    coordinates = [
                        city_info['coordinates'][0] + (random.uniform(-0.02, 0.02)),
                        city_info['coordinates'][1] + (random.uniform(-0.02, 0.02))
                    ]
                
                hotel_data = {
                    'id': i + 1,
                    'name': hotel.get('name', f'Hotel {i+1}'),
                    'price': price,
                    'currency': 'EUR',
                    'rating': round(hotel.get('reviewScore', 8.0) / 2, 1),  # Convert to 5-star scale
                    'coordinates': coordinates,
                    'address': hotel.get('address', city_info['name']),  # Real hotel address
                    'booking_url': f"https://booking.com/hotel/{hotel.get('id', '')}"
                }
                
                hotels.append(hotel_data)
            
            return {
                'success': True,
                'city': city_info['name'],
                'hotels': hotels,
                'total_found': len(hotels_data)
            }
        
        else:
            return {'error': f'API error: {response.status_code}'}
    
    except Exception as e:
        return {'error': f'Exception: {str(e)}'}

@app.route('/')
def home():
    """Simple test page"""
    return render_template_string('''
    <h1>🏨 ACTIONLY Backend API</h1>
    <p>Flask backend for European hotel search</p>
    <h3>Available endpoints:</h3>
    <ul>
        <li><a href="/api/hotels?city=stockholm&checkin=2025-07-14&checkout=2025-07-21">/api/hotels</a> - Get hotels for a city</li>
        <li><a href="/api/cities">/api/cities</a> - List all 29 cities</li>
        <li><a href="/test">/test</a> - Test Stockholm hotels</li>
    </ul>
    <p>Cities supported: {{ cities }}</p>
    ''', cities=list(CITIES.keys()))

@app.route('/api/cities')
def get_cities():
    """Get list of all supported cities"""
    return jsonify({
        'cities': {key: {'name': value['name'], 'coordinates': value['coordinates']} 
                  for key, value in CITIES.items()}
    })

@app.route('/api/hotels')
def get_hotels():
    """Main API endpoint for ACTIONLY frontend"""
    
    # Get parameters
    city = request.args.get('city', 'stockholm')
    checkin = request.args.get('checkin', '2025-07-14')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = int(request.args.get('adults', 2))
    rooms = int(request.args.get('rooms', 1))
    
    print(f"API Request: {city}, {checkin} to {checkout}, {adults} adults")
    
    # Get hotel data
    result = get_hotels_for_city(city, checkin, checkout, adults, rooms)
    
    return jsonify(result)

@app.route('/test')
def test_stockholm():
    """Test endpoint with Stockholm"""
    result = get_hotels_for_city('stockholm', '2025-07-14', '2025-07-21')
    return jsonify(result)

if __name__ == '__main__':
    print("🚀 Starting ACTIONLY Backend...")
    print("🏨 Supporting 29 European cities")
    print("🔗 Frontend will connect to: http://localhost:5000")
    print("📋 Test API: http://localhost:5000/test")
    
    import os
port = int(os.environ.get('PORT', 5000))
app.run(debug=True, host='0.0.0.0', port=port)