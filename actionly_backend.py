def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms):
    processed_hotels = []

    # Säkerställ att datan är korrekt
    data = hotels_data.get('data')
    if not data:
        return processed_hotels

    # Extrahera hotellegenskaper
    properties = []
    if isinstance(data, dict):
        properties = (
            data.get('propertySearch', {}).get('properties') or
            data.get('properties') or []
        )
    elif isinstance(data, list):
        properties = data

    # Loopa igenom varje hotell
    for i, hotel in enumerate(properties[:25]):
        if not isinstance(hotel, dict):
            continue

        # 🏨 Namn
        hotel_name = hotel.get('name') or f"Hotel {i+1}"

        # 🗺️ Koordinater med fallback
        coordinates = city_info.get('coordinates', [0, 0])
        mm = hotel.get('mapMarker', {}).get('latLong', {})
        coord = hotel.get('coordinate', {})

        lat = (
            mm.get('lat') or mm.get('latitude') or
            coord.get('lat') or coord.get('latitude') or
            coordinates[0]
        )
        lon = (
            mm.get('lon') or mm.get('longitude') or
            coord.get('lon') or coord.get('longitude') or
            coordinates[1]
        )
        try:
            coordinates = [
