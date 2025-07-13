def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms):
    processed_hotels = []
    if not hotels_data or 'data' not in hotels_data:
        return processed_hotels

    data = hotels_data['data']
    properties = []
    try:
        if isinstance(data, dict) and data.get('propertySearch'):
            properties = data['propertySearch'].get('properties', [])
        elif isinstance(data, dict) and data.get('properties'):
            properties = data['properties']
        elif isinstance(data, list):
            properties = data
    except Exception as e:
        print(f"Error accessing Hotels.com properties: {e}")
        return processed_hotels

    for i, hotel in enumerate(properties[:25]):
        if not hotel or not isinstance(hotel, dict):
            continue

        hotel_name = hotel.get('name') or f"Hotel {i+1}"

        # Koordinater
        coordinates = None
        try:
            mm = hotel.get('mapMarker') or {}
            ll = mm.get('latLong') or {}
            coordinates = [float(ll.get('lat') or ll.get('latitude')),
                           float(ll.get('lon') or ll.get('longitude'))]
        except:
            pass
        if not coordinates:
            coord = hotel.get('coordinate') or {}
            coordinates = [float(coord.get('lat') or coord.get('latitude', city_info['coordinates'][0])),
                           float(coord.get('lon') or coord.get('longitude', city_info['coordinates'][1]))]
        if not coordinates:
            base_lat, base_lng = city_info['coordinates']
            coordinates = [base_lat, base_lng]

        # Pris
        price = 'N/A'
        try:
            price_obj = hotel.get('price') or {}
            lead = price_obj.get('lead') or {}
            price = int(lead.get('amount', price))
        except:
            price = 'N/A'

        # Rating
        rating = 4.0
        try:
            rev = hotel.get('reviews') or hotel.get('guestReviews') or {}
            rating = float(rev.get('score') or rev.get('rating') or rating)
        except:
            rating = 4.0

        # URL
        property_id = hotel.get('id') or hotel.get('propertyId') or f"{i}"
        hotels_url = (
            f"https://hotels.com/h{property_id}.Hotel-Information?"
            f"checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
        )

        # 🏷️ Adress – säkert hanterad med fallback
        address = (
            (hotel.get('neighborhood') or {}).get('name') or
            (hotel.get('address') or {}).get('streetAddress') or
            city_info['name']
        )

        processed_hotels.append({
            'id': f"hotels_{property_id}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Hotels.com',
            'platform_logo': '🏛️',
            'booking_url': hotels_url,
            'source': 'hotels'
        })

    return processed_hotels
