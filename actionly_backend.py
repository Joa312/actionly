def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms):
    processed_hotels = []
    if not hotels_data or 'data' not in hotels_data:
        return processed_hotels

    # Hämta properties
    data = hotels_data['data']
    properties = []
    try:
        if isinstance(data, dict) and 'propertySearch' in data and data['propertySearch']:
            properties = data['propertySearch'].get('properties', [])
        elif isinstance(data, dict) and 'properties' in data:
            properties = data['properties']
        elif isinstance(data, list):
            properties = data
    except Exception as e:
        print(f"Error accessing Hotels.com properties: {e}")
        return processed_hotels

    for i, hotel in enumerate(properties[:25]):
        if not hotel or not isinstance(hotel, dict):
            continue

        # Namn
        hotel_name = hotel.get('name') or f"Hotel {i+1}"

        # Koordinater
        coordinates = None
        try:
            map_marker = hotel.get('mapMarker', {}) or {}
            latLong = map_marker.get('latLong') or {}
            coordinates = [
                float(latLong.get('lat') or latLong.get('latitude')),
                float(latLong.get('lon') or latLong.get('longitude'))
            ]
        except:
            pass
        if not coordinates:
            coord = hotel.get('coordinate') or {}
            coordinates = [
                float(coord.get('lat') or coord.get('latitude', city_info['coordinates'][0])),
                float(coord.get('lon') or coord.get('longitude', city_info['coordinates'][1]))
            ]
        if not coordinates:
            base_lat, base_lng = city_info['coordinates']
            coordinates = [base_lat, base_lng]

        # Pris
        price = 'N/A'
        try:
            price_obj = hotel.get('price') or {}
            lead = price_obj.get('lead') or {}
            price = int(lead.get('amount') or price)
        except:
            price = 'N/A'

        # Rating
        rating = 4.0
        try:
            reviews = hotel.get('reviews') or hotel.get('guestReviews') or {}
            rating = float(reviews.get('score') or reviews.get('rating') or rating)
        except:
            rating = 4.0

        # URL
        property_id = hotel.get('id') or hotel.get('propertyId') or f"{i}"
        hotels_url = (f"https://hotels.com/h{property_id}.Hotel-Information?"
                      f"checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0")

        # Adress – undvik NoneType
        address = city_info['name']
        try:
            neighborhood = hotel.get('neighborhood')
            if isinstance(neighborhood, dict) and neighborhood.get('name'):
                address = neighborhood['name']
            else:
                addr_obj = hotel.get('address')
                if isinstance(addr_obj, dict):
                    address = (addr_obj.get('streetAddress')
                               or addr_obj.get('locality')
                               or addr_obj.get('region')
                               or address)
                elif isinstance(addr_obj, str) and addr_obj:
                    address = addr_obj
                else:
                    location = hotel.get('location') or {}
                    if isinstance(location, dict):
                        address = location.get('address') or location.get('name') or address
        except Exception as e:
            print(f"Address parsing error for {hotel_name}: {e}")

        # Sätt ihop hotelldata
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
