import requests

api_key = 'e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999'
stockholm_id = 'eyJjaXR5X25hbWUiOiJTdG9ja2hvbG0iLCJjb3VudHJ5IjoiU3dlZGVuIiwiZGVzdF9pZCI6Ii0yNTI0Mjc5IiwiZGVzdF90eXBlIjoiY2l0eSJ9'

url = 'https://booking-com18.p.rapidapi.com/stays/search'
params = {
    'locationId': stockholm_id,
    'checkinDate': '2025-07-14',
    'checkoutDate': '2025-07-21',
    'adults': '2',
    'rooms': '1',
    'currency': 'EUR'
}
headers = {
    'x-rapidapi-key': api_key,
    'x-rapidapi-host': 'booking-com18.p.rapidapi.com'
}

print('Testing Stockholm hotels...')
response = requests.get(url, headers=headers, params=params)
print(f'Status: {response.status_code}')

if response.status_code == 200:
    data = response.json()
    hotels = data.get('data', [])
    print(f'Found {len(hotels)} Stockholm hotels!')
    for i, hotel in enumerate(hotels[:3], 1):
        print(f'{i}. {hotel.get("name", "Unknown")}')
else:
    print('Failed')
