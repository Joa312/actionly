# ... kod tidigare oförändrad ...

def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms):
    """Process Hotels.com hotel data (v2 API format) med felhantering"""
    processed_hotels = []
    # ... tidigare parsingkod ...

    for i, hotel in enumerate(properties[:25]):
        try:
            # ... namn-, koordinats- och prisutvinning ...

            # Hämta adress på ett säkert sätt
            address = city_info['name']
            try:
                neighborhood = hotel.get('neighborhood')
                if neighborhood and isinstance(neighborhood, dict) and neighborhood.get('name'):
                    address = neighborhood['name']
                else:
                    addr_obj = hotel.get('address')
                    if isinstance(addr_obj, dict):
                        address = addr_obj.get('streetAddress') or addr_obj.get('locality') or addr_obj.get('region') or address
                    elif isinstance(addr_obj, str):
                        address = addr_obj
                    else:
                        location = hotel.get('location')
                        if isinstance(location, dict):
                            address = location.get('address') or location.get('name') or address
            except Exception as e:
                print(f"Address parsing error for {hotel_name}: {e}")
                address = city_info['name']

            # Skapa URL
            property_id = hotel.get('id') or hotel.get('propertyId') or f'hotel_{i}'
            hotels_url = f"https://hotels.com/h{property_id}.Hotel-Information?checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"

            # Bygg objektet
            processed_hotel = {
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
            }
            processed_hotels.append(processed_hotel)

        except Exception as e:
            print(f"Error processing Hotels.com hotel {i}: {e}")
            continue

    return processed_hotels
