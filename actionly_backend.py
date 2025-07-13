def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms):
    processed_hotels = []
    if not hotels_data or 'data' not in hotels_data:
        return processed_hotels

    data = hotels_data['data']
    properties = []

    try:
        if isinstance(data, dict):
            properties = (
                data.get('propertySearch', {}).get('properties') or
                data.get('properties') or
                []
            )
        elif isinstance(data, list):
            properties = data
    except Exception as e:
        print(f"Error accessing Hotels.com properties: {e}")
        return processed_hotels

    for i, hotel in enumerate(properties[:25]):
        if not hotel or not isinstance(hotel, dict):
            continue

        # 🏨 Hotellnamn
        hotel_name = hotel.get('name') or f"Hotel {i+1}"

        # 🗺️ Koordinater
        coordinates = None
        try:
            mm = hotel.get('mapMarker', {})
            ll = mm.get('latLong', {})
            lat = float(ll.get('lat') or ll.get('latitude', 0))
            lon = float(ll.get('lon') or ll.get('longitude', 0))
            coordinates = [lat, lon]
        except:
            pass

        if not coordinates or coordinates == [0, 0]:
            coord = hotel.get('coordinate', {})
            lat = float(coord.get('lat') or coord.get('latitude', city_info['coordinates'][0]))
            lon = float(coord.get('lon') or coord.get('longitude', city_info['coordinates'][1]))
            coordinates = [lat, lon]

        if not coordinates or coordinates == [0, 0]:
            coordinates = city_info['coordinates']

        # 💰 Pris
        price = 'N/A'
        try:
            price_obj = hotel.get('price', {})
            lead = price_obj.get('lead', {})
            price = int(lead.get('amount', price))
        except:
            pass

        # ⭐ Betyg
        rating = 4.0
        try:
            reviews = hotel.get('reviews') or hotel.get('guestReviews') or {}
            rating = float(reviews.get('score') or reviews.get('rating') or rating)
        except:
            pass

        # 🔗 URL till bokning
        property_id = hotel.get('id') or hotel.get('propertyId') or f"{i}"
        hotels_url = (
            f"https://hotels.com/h{property_id}.Hotel-Information?"
            f"checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
        )

        # 🏷️ Adress med robust fallback
        try:
            neighborhood = hotel.get('neighborhood')
            if isinstance(neighborhood, dict):
                address = neighborhood.get('name', city_info['name'])
            else:
                address = (hotel.get('address', {}).get('streetAddress') or city_info['name'])
        except:
            address = city_info['name']

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
