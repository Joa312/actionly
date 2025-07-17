#!/usr/bin/env python3
"""
STAYFINDR Backend API - Dual Integration
European Hotel Search Engine med BÅDE Booking.com OCH TripAdvisor
Version: 2.0 - Dual Platform Edition
"""

import csv
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus

import requests
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Logging konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app initiering
app = FastAPI(
    title="STAYFINDR API - Dual Platform",
    description="European Hotel Search with BOTH Booking.com AND TripAdvisor integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# API konfiguration
BOOKING_HOST = "booking-com15.p.rapidapi.com"
TRIPADVISOR_HOST = "tripadvisor1.p.rapidapi.com"
API_KEY = os.getenv("RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")

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

# TripAdvisor location mappings (exempel för testing)
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
    'prague': '274707'
}

# Pydantic models
class HotelSearchRequest(BaseModel):
    city: str = Field(..., min_length=2, max_length=50, description="City name")
    checkin_date: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    checkout_date: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    room_number: int = Field(1, ge=1, le=10, description="Number of rooms")
    guest_number: int = Field(2, ge=1, le=20, description="Number of guests")
    room_type: Optional[str] = Field(None, description="Room type filter")
    
    @validator('checkin_date', 'checkout_date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('checkout_date')
    def validate_checkout_after_checkin(cls, v, values):
        if 'checkin_date' in values:
            checkin = datetime.strptime(values['checkin_date'], '%Y-%m-%d')
            checkout = datetime.strptime(v, '%Y-%m-%d')
            if checkout <= checkin:
                raise ValueError('Checkout date must be after checkin date')
            if (checkout - checkin).days > 30:
                raise ValueError('Stay cannot be longer than 30 days')
        return v

class HotelResponse(BaseModel):
    id: str
    name: str
    address: str
    coordinates: List[float]
    price: str
    rating: float
    booking_url: str  # Booking.com URL
    tripadvisor_url: str  # TripAdvisor URL - NY!
    reviews_count: Optional[int] = None
    room_type_match: Optional[str] = None

class SearchResponse(BaseModel):
    city: str
    hotels: List[HotelResponse]
    total_found: int
    search_params: Dict[str, Any]
    room_filter: Optional[str] = None
    data_sources: List[str] = ["Booking.com", "TripAdvisor"]

# Helper functions
def validate_api_key():
    """Validera API-nyckel"""
    if API_KEY == "YOUR_RAPIDAPI_KEY" or not API_KEY:
        logger.error("API key not configured")
        return False
    return True

def get_city_id(city_name: str) -> Optional[str]:
    """Hämta city ID från CSV-fil för Booking.com"""
    csv_file = "cities.csv"
    
    if not os.path.exists(csv_file):
        logger.error(f"Cities CSV file not found: {csv_file}")
        return None
    
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
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Booking.com API error: {response.status_code}")
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
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"TripAdvisor API error: {response.status_code}")
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
        # Kontrollera om hotellnamnen överlappar med minst 3 ord
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
                           adults: int, rooms: int, room_type: Optional[str] = None) -> List[HotelResponse]:
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
            hotel_response = HotelResponse(
                id=booking_hotel.get('id', f'hotel_{i}'),
                name=hotel_name,
                address=address,
                coordinates=coordinates,
                price=price,
                rating=rating,
                booking_url=booking_url,
                tripadvisor_url=tripadvisor_url,  # NY: TripAdvisor URL
                reviews_count=reviews_count,
                room_type_match=room_match
            )
            
            processed_hotels.append(hotel_response)
            
        except Exception as e:
            logger.error(f"Error processing hotel {i}: {e}")
            continue
    
    return processed_hotels

# API Endpoints
@app.get("/", response_model=Dict[str, Any])
def root():
    """Root endpoint med API information"""
    return {
        "message": "STAYFINDR Backend API v2.0 - Dual Platform Edition",
        "status": "running",
        "data_sources": ["Booking.com", "TripAdvisor"],
        "features": ["Hotel search", "Dual booking links", "Room type filter"],
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    api_key_valid = validate_api_key()
    cities_file_exists = os.path.exists("cities.csv")
    
    return {
        "status": "healthy" if api_key_valid and cities_file_exists else "unhealthy",
        "api_key": "configured" if api_key_valid else "missing",
        "cities_file": "found" if cities_file_exists else "missing",
        "data_sources": ["Booking.com", "TripAdvisor"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/hotels", response_model=SearchResponse)
def search_hotels(search: HotelSearchRequest):
    """Sök hotell från BÅDA Booking.com OCH TripAdvisor"""
    
    # Validera API-nyckel
    if not validate_api_key():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API service not configured properly"
        )
    
    # Hämta Booking.com city ID
    booking_dest_id = get_city_id(search.city)
    if not booking_dest_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City '{search.city}' not found in Booking.com database"
        )
    
    # Hämta TripAdvisor location ID
    tripadvisor_location_id = TRIPADVISOR_LOCATIONS.get(search.city.lower())
    
    # Validera rumstyp
    if search.room_type and search.room_type not in ROOM_TYPE_MAPPING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid room type. Available: {list(ROOM_TYPE_MAPPING.keys())}"
        )
    
    try:
        # Parallella API-anrop (asynkront skulle vara bättre)
        booking_data = search_hotels_booking_api(
            booking_dest_id, search.checkin_date, search.checkout_date,
            search.guest_number, search.room_number
        )
        
        tripadvisor_data = None
        if tripadvisor_location_id:
            tripadvisor_data = get_tripadvisor_hotels(tripadvisor_location_id)
        
        # Kontrollera Booking.com data
        if not booking_data or 'data' not in booking_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hotels found from Booking.com"
            )
        
        booking_hotels = booking_data.get('data', [])
        tripadvisor_hotels = tripadvisor_data.get('data', []) if tripadvisor_data else []
        
        if not booking_hotels:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hotels found for the specified criteria"
            )
        
        # Bearbeta data från BÅDA källor
        processed_hotels = process_dual_hotel_data(
            booking_hotels, tripadvisor_hotels, search.city,
            search.checkin_date, search.checkout_date, 
            search.guest_number, search.room_number, search.room_type
        )
        
        # Skapa response
        return SearchResponse(
            city=search.city,
            hotels=processed_hotels,
            total_found=len(processed_hotels),
            search_params={
                "checkin": search.checkin_date,
                "checkout": search.checkout_date,
                "guests": search.guest_number,
                "rooms": search.room_number
            },
            room_filter=search.room_type,
            data_sources=["Booking.com", "TripAdvisor"]
        )
        
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Hotel search service timeout"
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hotel search service unavailable"
        )

@app.get("/room-types")
def get_room_types():
    """Hämta tillgängliga rumstyper"""
    return {
        "room_types": ROOM_TYPE_MAPPING,
        "available_types": list(ROOM_TYPE_MAPPING.keys())
    }

@app.get("/cities")
def get_supported_cities():
    """Hämta alla städer"""
    csv_file = "cities.csv"
    
    if not os.path.exists(csv_file):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cities database not available"
        )
    
    cities = []
    try:
        with open(csv_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                city_key = row["city"].lower()
                cities.append({
                    "city": row["city"],
                    "booking_dest_id": row["dest_id"],
                    "tripadvisor_location_id": TRIPADVISOR_LOCATIONS.get(city_key),
                    "country_code": COUNTRY_CODES.get(city_key, "en-gb"),
                    "both_platforms": city_key in TRIPADVISOR_LOCATIONS
                })
    except Exception as e:
        logger.error(f"Error reading cities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading cities database"
        )
    
    return {
        "cities": cities,
        "total": len(cities),
        "dual_platform_cities": len([c for c in cities if c["both_platforms"]])
    }

@app.get("/test")
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
            
            return {
                "status": "success",
                "test_city": "Stockholm",
                "booking_hotels_found": len(booking_hotels),
                "tripadvisor_hotels_found": len(tripadvisor_hotels),
                "sample_hotels": processed,
                "data_sources": ["Booking.com", "TripAdvisor"]
            }
        else:
            return {
                "status": "error",
                "message": "No Booking.com data found"
            }
            
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return {
            "status": "error", 
            "message": str(e)
        }

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# Development server
if __name__ == "__main__":
    logger.info("Starting STAYFINDR Backend API v2.0 - Dual Platform Edition")
    logger.info("Supporting BOTH Booking.com AND TripAdvisor integration")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
