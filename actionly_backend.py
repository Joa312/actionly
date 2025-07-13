def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms):
    processed_hotels = []
    if not isinstance(hotels_data, dict) or 'data' not in hotels_data:
        return processed_hotels

    data = hotels_data.get('data')
    properties = []

    # 🎯 Extrahera hotellista
    if isinstance(data, dict):
        properties = (
            data.get('propertySearch', {}).get('properties') or
            data.get('properties') or []
        )
    elif isinstance(data, list):
        properties = data

    for i, hotel in enumerate(properties[:25]):
        if not isinstance(hotel, dict):
            continue

        # 🏨 Hotellnamn
        hotel_name = hotel.get('name') or f"Hotel {i+1}"

        # 🗺️ Koordinater med trygga fallbacks
        coordinates = city_info.get('coordinates', [0.0, 0.0])
        lat = (
            hotel.get('mapMarker', {}).get('latLong', {}).get('lat') or
            hotel.get('mapMarker', {}).get('latLong', {}).get('latitude') or
            hotel.get('coordinate', {}).get('lat') or
            hotel.get('coordinate', {}).get('latitude')
        )
        lon = (
            hotel.get('mapMarker', {}).get('latLong', {}).get('lon') or
            hotel.get('mapMarker', {}).get('latLong', {}).get('longitude') or
            hotel.get('coordinate', {}).get('lon') or
            hotel.get('coordinate', {}).get('longitude')
        )
        try:
            coordinates = [float(lat), float(lon)]
        except (TypeError, ValueError):
            pass  # behåll stadens koordinater som fallback

        # 💰 Pris
        price = hotel.get('price', {}).get('lead', {}).get('amount')
        try:
            price = int(price)
        except (TypeError, ValueError):
            price = 'N/A'

        # ⭐ Gästbetyg
        rating = hotel.get('reviews', {}).get('score') or hotel.get('guestReviews', {}).get('rating')
        try:
            rating = float(rating)
        except (TypeError, ValueError):
            rating = 4.0

        # 🔗 Bokningslänk
        property_id = hotel.get('id') or hotel.get('propertyId') or str(i)
        hotels_url = (
            f"https://hotels.com/h{property_id}.Hotel-Information?"
            f"checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
        )

        # 🏷️ Adress med säker kontroll
        address = city_info.get('name')
        neighborhood = hotel.get('neighborhood')
        if isinstance(neighborhood, dict):
            address = neighborhood.get('name') or address
        else:
            street = hotel.get('address', {}).get('streetAddress')
            if street:
                address = street

        # 📦 Samla information
        processed_hotels.append({
            'id': f"hotels_{property_id}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Hotels.com',
            'platform_logo': '🏛️',
            'booking_url': hotels
