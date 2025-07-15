<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>STAYFINDR - European Hotel Search</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" 
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" 
          crossorigin=""/>
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0; padding: 20px; min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { 
            font-size: 3rem; 
            font-weight: 700; 
            margin-bottom: 10px;
            background: linear-gradient(45deg, #ff6b6b, #feca57, #48dbfb, #ff9ff3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        
        .status { 
            text-align: center; color: white; margin-bottom: 20px; 
            padding: 10px; border-radius: 8px;
            background: rgba(255,255,255,0.1);
        }
        
        .search-container { 
            background: rgba(255,255,255,0.95); 
            border-radius: 20px; padding: 30px; margin-bottom: 30px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .search-form {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            align-items: end;
            margin-bottom: 25px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            margin-bottom: 5px;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .form-group select, .form-group input {
            padding: 12px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .form-group select:focus, .form-group input:focus {
            outline: none;
            border-color: #3498db;
        }

        /* DUAL SOURCE SEARCH BUTTONS */
        .dual-search-section {
            border-top: 2px solid #ecf0f1;
            padding-top: 25px;
            margin-top: 20px;
        }
        
        .search-method-label {
            text-align: center;
            font-size: 1.1rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        
        .dual-search-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .search-btn {
            padding: 18px 25px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .search-btn:disabled {
            cursor: not-allowed;
            opacity: 0.6;
            transform: none !important;
        }
        
        .booking-btn {
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            border: 2px solid transparent;
        }
        
        .booking-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(30, 60, 114, 0.3);
            background: linear-gradient(135deg, #2a5298, #1e3c72);
        }
        
        .tripadvisor-btn {
            background: linear-gradient(135deg, #00af87, #34b896);
            color: white;
            border: 2px solid transparent;
        }
        
        .tripadvisor-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 175, 135, 0.3);
            background: linear-gradient(135deg, #34b896, #00af87);
        }
        
        .search-btn .btn-title {
            display: block;
            font-size: 1.1rem;
            margin-bottom: 4px;
        }
        
        .search-btn .btn-subtitle {
            display: block;
            font-size: 0.85rem;
            opacity: 0.9;
            font-weight: 400;
        }
        
        .search-btn.loading {
            pointer-events: none;
        }
        
        .search-btn.loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid transparent;
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* ROOM TYPE STATUS */
        .room-status {
            background: #e8f5e8;
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
            text-align: center;
            font-size: 0.9rem;
            color: #27ae60;
            border: 1px solid #d5e7d5;
        }
        
        /* MAIN CONTENT AREA */
        .main-content { 
            display: grid; 
            grid-template-columns: 1fr 400px; 
            gap: 30px; 
            height: 600px; 
        }
        
        #map { 
            border-radius: 15px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .hotels-panel { 
            background: rgba(255,255,255,0.95); 
            border-radius: 15px; 
            padding: 25px; 
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        .hotels-panel h3 {
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .source-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .source-booking {
            background: #1e3c72;
            color: white;
        }
        
        .source-tripadvisor {
            background: #00af87;
            color: white;
        }
        
        .hotel-card { 
            background: white; 
            border-radius: 10px; 
            padding: 15px; 
            margin: 10px 0; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
            border-left: 4px solid transparent;
        }
        
        .hotel-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .hotel-card.highlighted {
            border: 2px solid #3498db;
            background: #f8f9fa;
        }
        
        .hotel-card.source-booking {
            border-left-color: #1e3c72;
        }
        
        .hotel-card.source-tripadvisor {
            border-left-color: #00af87;
        }
        
        .hotel-name {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
            font-size: 1.1rem;
        }
        
        .hotel-details {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 8px;
        }
        
        .room-type-display {
            background: #f39c12;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            display: inline-block;
            margin-bottom: 10px;
        }
        
        .price-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .price {
            font-size: 1.3rem;
            font-weight: 600;
            color: #27ae60;
        }
        
        .rating {
            color: #f39c12;
            font-weight: 500;
        }
        
        .hotel-actions {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }
        
        .action-btn {
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: background-color 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            flex: 1;
        }
        
        .book-btn.booking-source {
            background: #1e3c72;
            color: white;
        }
        
        .book-btn.booking-source:hover {
            background: #2a5298;
        }
        
        .book-btn.tripadvisor-source {
            background: #00af87;
            color: white;
        }
        
        .book-btn.tripadvisor-source:hover {
            background: #34b896;
        }
        
        .loading {
            text-align: center;
            color: #7f8c8d;
            padding: 20px;
        }
        
        .error {
            text-align: center;
            color: #e74c3c;
            padding: 20px;
            background: #fdf2f2;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .success-indicator {
            background: #d4edda;
            color: #155724;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: center;
        }

        /* MOBILE RESPONSIVENESS */
        @media (max-width: 768px) {
            body { padding: 10px !important; }
            .container { padding: 5px !important; }
            .header h1 { font-size: 2.5rem !important; }
            .header p { font-size: 1rem !important; }
            .search-container { padding: 20px !important; margin-bottom: 15px !important; }
            .search-form { grid-template-columns: 1fr !important; gap: 10px !important; }
            
            .dual-search-buttons {
                grid-template-columns: 1fr !important;
                gap: 15px !important;
            }
            
            .search-btn {
                padding: 16px 20px !important;
                font-size: 15px !important;
            }
            
            .form-group select, .form-group input, .search-btn {
                min-height: 44px !important;
                font-size: 16px !important;
                padding: 12px !important;
            }
            
            .main-content {
                grid-template-columns: 1fr !important;
                height: auto !important;
                gap: 15px !important;
            }
            
            #map {
                height: 300px !important;
                margin-bottom: 15px !important;
            }
            
            .hotels-panel {
                height: 500px !important;
                padding: 15px !important;
            }
            
            .hotel-card {
                padding: 12px !important;
                margin: 8px 0 !important;
            }
            
            .hotel-name { font-size: 1rem !important; }
            .price { font-size: 1.1rem !important; }
            
            .hotel-actions {
                flex-wrap: wrap !important;
                gap: 5px !important;
            }
            
            .action-btn {
                flex: 1 !important;
                min-width: 120px !important;
                padding: 10px 8px !important;
                font-size: 0.8rem !important;
            }
            
            .status { font-size: 0.9rem !important; padding: 8px !important; }
        }

        @media (max-width: 480px) {
            .header h1 { font-size: 2rem !important; }
            .search-container { padding: 15px !important; }
            #map { height: 250px !important; }
            .hotels-panel { height: 400px !important; padding: 10px !important; }
            .hotel-card { padding: 10px !important; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>STAYFINDR</h1>
            <p>Save Time & Money: See Today's Hotel Prices Across Europe</p>
        </div>
            
        <div class="status" id="connectionStatus">
            🔗 Connecting to STAYFINDR backend...
        </div>

        <div class="search-container">
            <form id="searchForm" class="search-form">
                <div class="form-group">
                    <label for="city">City</label>
                    <select id="city">
                        <option value="stockholm">Stockholm, Sweden</option>
                        <option value="paris">Paris, France</option>
                        <option value="london">London, UK</option>
                        <option value="amsterdam">Amsterdam, Netherlands</option>
                        <option value="barcelona">Barcelona, Spain</option>
                        <option value="rome">Rome, Italy</option>
                        <option value="berlin">Berlin, Germany</option>
                        <option value="copenhagen">Copenhagen, Denmark</option>
                        <option value="vienna">Vienna, Austria</option>
                        <option value="prague">Prague, Czech Republic</option>
                        <option value="madrid">Madrid, Spain</option>
                        <option value="milano">Milano, Italy</option>
                        <option value="zurich">Zürich, Switzerland</option>
                        <option value="oslo">Oslo, Norway</option>
                        <option value="helsinki">Helsinki, Finland</option>
                        <option value="warsaw">Warsaw, Poland</option>
                        <option value="budapest">Budapest, Hungary</option>
                        <option value="dublin">Dublin, Ireland</option>
                        <option value="lisbon">Lisbon, Portugal</option>
                        <option value="brussels">Brussels, Belgium</option>
                        <option value="athens">Athens, Greece</option>
                        <option value="munich">Munich, Germany</option>
                        <option value="lyon">Lyon, France</option>
                        <option value="florence">Florence, Italy</option>
                        <option value="edinburgh">Edinburgh, Scotland</option>
                        <option value="nice">Nice, France</option>
                        <option value="palma">Palma, Spain</option>
                        <option value="santorini">Santorini, Greece</option>
                        <option value="ibiza">Ibiza, Spain</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="roomType">Room Type</label>
                    <select id="roomType">
                        <option value="single">Single Room (1 guest)</option>
                        <option value="double" selected>Double Room (2 guests)</option>
                        <option value="family">Family Room (3-4 guests)</option>
                        <option value="junior_suite">Junior Suite (2 guests)</option>
                        <option value="suite">Suite/Apartment (2-4 guests)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="checkin">Check-in</label>
                    <input type="date" id="checkin" required>
                </div>
                
                <div class="form-group">
                    <label for="checkout">Check-out</label>
                    <input type="date" id="checkout" required>
                </div>
                
                <div class="form-group">
                    <label for="guests">Guests</label>
                    <select id="guests">
                        <option value="1">1 Guest</option>
                        <option value="2" selected>2 Guests</option>
                        <option value="3">3 Guests</option>
                        <option value="4">4 Guests</option>
                    </select>
                </div>
            </form>
            
            <div class="room-status" id="roomStatus">
                Double Room - Perfect for couples and business travelers - Ready to search!
            </div>
            
            <div class="dual-search-section">
                <div class="search-method-label">Choose Your Search Method:</div>
                <div class="dual-search-buttons">
                    <button type="button" class="search-btn booking-btn" id="searchBooking">
                        <span class="btn-title">🏨 Search Booking.com</span>
                        <span class="btn-subtitle">Real-time prices & instant booking</span>
                    </button>
                    
                    <button type="button" class="search-btn tripadvisor-btn" id="searchTripAdvisor">
                        <span class="btn-title">⭐ Search TripAdvisor</span>
                        <span class="btn-subtitle">Reviews & ratings focused</span>
                    </button>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div id="map"></div>
            <div class="hotels-panel">
                <h3 id="hotelsTitle">Hotels</h3>
                <div id="hotelsList">
                    <div class="loading">Choose a search method above to find hotels from your preferred source</div>
                </div>
                <div id="loadMoreContainer" style="display: none; text-align: center; margin-top: 15px;">
                    <button id="loadMoreBtn" class="search-btn" style="width: 100%;">
                        📋 Show More Hotels
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map;
        let currentMarkers = [];
        let currentHotels = [];
        let allHotelsData = [];
        let currentlyShowing = 10;
        let currentSource = null;
        const BACKEND_URL = 'https://actionly.onrender.com';

        // Room type configurations
        const ROOM_TYPES = {
            'single': {
                name: 'Single Room',
                description: 'Comfortable single accommodation',
                guests: 1
            },
            'double': {
                name: 'Double Room', 
                description: 'Perfect for couples and business travelers',
                guests: 2
            },
            'family': {
                name: 'Family Room',
                description: 'Spacious accommodation for families', 
                guests: 4
            },
            'junior_suite': {
                name: 'Junior Suite',
                description: 'Spacious room with sitting area - upgraded comfort',
                guests: 2
            },
            'suite': {
                name: 'Suite/Apartment',
                description: 'Luxury accommodation with separate living area',
                guests: 3
            }
        };

        // Wait for Leaflet to load properly
        function waitForLeaflet() {
            return new Promise((resolve) => {
                function checkLeaflet() {
                    if (typeof L !== 'undefined') {
                        console.log('✅ Leaflet loaded successfully');
                        resolve();
                    } else {
                        console.log('⏳ Waiting for Leaflet...');
                        setTimeout(checkLeaflet, 100);
                    }
                }
                checkLeaflet();
            });
        }

        // Initialize the application
        function initializeApp() {
            console.log('🚀 Initializing STAYFINDR Dual-Source...');
            
            testBackendConnection();
            initMap();
            setupEventListeners();
            setDefaultDates();
            updateRoomStatus();
            
            console.log('✅ STAYFINDR Dual-Source initialized successfully');
        }

        async function testBackendConnection() {
            try {
                const response = await fetch(`${BACKEND_URL}/api/cities`);
                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('connectionStatus').innerHTML = `✅ Connected to STAYFINDR backend - ${data.total} cities available with dual-source search!`;
                    document.getElementById('connectionStatus').className = 'status success-indicator';
                } else {
                    throw new Error('Backend not responding');
                }
            } catch (error) {
                document.getElementById('connectionStatus').innerHTML = '❌ Backend offline - Demo mode active';
                document.getElementById('connectionStatus').className = 'status error';
            }
        }

        function initMap() {
            try {
                map = L.map('map').setView([59.3293, 18.0686], 6);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
                console.log('🗺️ Map initialized successfully');
            } catch (error) {
                console.error('Map initialization failed:', error);
            }
        }

        function setupEventListeners() {
            // Room type change listener
            const roomTypeSelect = document.getElementById('roomType');
            const guestsSelect = document.getElementById('guests');
            
            roomTypeSelect.addEventListener('change', function() {
                const selectedType = this.value;
                const roomConfig = ROOM_TYPES[selectedType];
                
                // Auto-update guests based on room type
                guestsSelect.value = roomConfig.guests.toString();
                
                updateRoomStatus();
            });

            // Dual search button listeners
            document.getElementById('searchBooking').addEventListener('click', function() {
                searchHotels('booking');
            });

            document.getElementById('searchTripAdvisor').addEventListener('click', function() {
                searchHotels('tripadvisor');
            });

            // Load more button
            const loadMoreBtn = document.getElementById('loadMoreBtn');
            if (loadMoreBtn) {
                loadMoreBtn.addEventListener('click', function() {
                    showMoreHotels();
                });
            }

            console.log('📋 Event listeners setup for dual-source search');
        }

        function updateRoomStatus() {
            const roomType = document.getElementById('roomType').value;
            const roomConfig = ROOM_TYPES[roomType];
            const statusDiv = document.getElementById('roomStatus');
            
            statusDiv.innerHTML = `${roomConfig.name} - ${roomConfig.description} - Ready to search!`;
        }

        function setDefaultDates() {
            const today = new Date();
            const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
            
            document.getElementById('checkin').value = today.toISOString().split('T')[0];
            document.getElementById('checkout').value = tomorrow.toISOString().split('T')[0];
        }

        async function searchHotels(source) {
            const city = document.getElementById('city').value;
            const roomType = document.getElementById('roomType').value;
            const checkin = document.getElementById('checkin').value;
            const checkout = document.getElementById('checkout').value;
            const guests = document.getElementById('guests').value;

            console.log(`🔍 Searching hotels via ${source}: ${city}, ${checkin} to ${checkout}, ${guests} guests, ${roomType}`);

            const bookingBtn = document.getElementById('searchBooking');
            const tripAdvisorBtn = document.getElementById('searchTripAdvisor');
            const hotelsList = document.getElementById('hotelsList');
            const hotelsTitle = document.getElementById('hotelsTitle');

            // Set loading state for the clicked button
            if (source === 'booking') {
                bookingBtn.disabled = true;
                bookingBtn.classList.add('loading');
                bookingBtn.innerHTML = '<span class="btn-title">🔄 Searching...</span><span class="btn-subtitle">Fetching Booking.com data</span>';
            } else {
                tripAdvisorBtn.disabled = true;
                tripAdvisorBtn.classList.add('loading');
                tripAdvisorBtn.innerHTML = '<span class="btn-title">🔄 Searching...</span><span class="btn-subtitle">Fetching TripAdvisor data</span>';
            }

            // Update UI
            hotelsList.innerHTML = `<div class="loading">🔍 Searching ${source === 'booking' ? 'Booking.com' : 'TripAdvisor'} for hotels...</div>`;
            
            const sourceLabel = source === 'booking' ? 'Booking.com' : 'TripAdvisor';
            const badgeClass = source === 'booking' ? 'source-booking' : 'source-tripadvisor';
            hotelsTitle.innerHTML = `Hotels in ${city} <span class="source-badge ${badgeClass}">${sourceLabel}</span>`;

            try {
                // Use different endpoints for different sources
                const endpoint = source === 'booking' ? 
                    `/api/hotels/booking` : 
                    `/api/hotels/tripadvisor`;
                    
                const response = await fetch(`${BACKEND_URL}${endpoint}?city=${city}&checkin=${checkin}&checkout=${checkout}&adults=${guests}&rooms=1&room_type=${roomType}`);
                
                if (!response.ok) {
                    throw new Error(`${sourceLabel} API error: ${response.status}`);
                }

                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                if (data.hotels && data.hotels.length > 0) {
                    allHotelsData = data.hotels;
                    currentSource = source;
                    currentlyShowing = Math.min(10, data.hotels.length);
                    
                    displayHotels(data.hotels.slice(0, currentlyShowing), data.city, source);
                    updateMap(data.hotels.slice(0, currentlyShowing));
                    
                    const loadMoreContainer = document.getElementById('loadMoreContainer');
                    if (data.hotels.length > currentlyShowing) {
                        loadMoreContainer.style.display = 'block';
                        updateLoadMoreButton();
                    } else {
                        loadMoreContainer.style.display = 'none';
                    }
                    
                    document.getElementById('connectionStatus').innerHTML = 
                        `✅ Found ${data.total_found} hotels from ${sourceLabel} in ${data.city}! (Showing ${currentlyShowing})`;
                    document.getElementById('connectionStatus').className = 'status success-indicator';
                } else {
                    hotelsList.innerHTML = `<div class="error">No hotels found on ${sourceLabel} for this city and dates.</div>`;
                    document.getElementById('loadMoreContainer').style.display = 'none';
                }

            } catch (error) {
                console.error(`${sourceLabel} search error:`, error);
                hotelsList.innerHTML = `<div class="error">Error searching ${sourceLabel}: ${error.message}</div>`;
                
                document.getElementById('connectionStatus').innerHTML = `❌ ${sourceLabel} search failed - Try the other source`;
                document.getElementById('connectionStatus').className = 'status error';
            }

            // Reset button states
            resetSearchButtons();
        }

        function resetSearchButtons() {
            const bookingBtn = document.getElementById('searchBooking');
            const tripAdvisorBtn = document.getElementById('searchTripAdvisor');
            
            // Reset Booking.com button
            bookingBtn.disabled = false;
            bookingBtn.classList.remove('loading');
            bookingBtn.innerHTML = '<span class="btn-title">🏨 Search Booking.com</span><span class="btn-subtitle">Real-time prices & instant booking</span>';
            
            // Reset TripAdvisor button
            tripAdvisorBtn.disabled = false;
            tripAdvisorBtn.classList.remove('loading');
            tripAdvisorBtn.innerHTML = '<span class="btn-title">⭐ Search TripAdvisor</span><span class="btn-subtitle">Reviews & ratings focused</span>';
        }

        function showMoreHotels() {
            const nextBatch = Math.min(currentlyShowing + 10, allHotelsData.length);
            const hotelsToShow = allHotelsData.slice(0, nextBatch);
            
            currentlyShowing = nextBatch;
            
            displayHotels(hotelsToShow, '', currentSource);
            updateMap(hotelsToShow);
            updateLoadMoreButton();
            
            document.getElementById('connectionStatus').innerHTML = 
                `✅ Showing ${currentlyShowing} of ${allHotelsData.length} hotels from ${currentSource === 'booking' ? 'Booking.com' : 'TripAdvisor'}`;
        }

        function updateLoadMoreButton() {
            const loadMoreBtn = document.getElementById('loadMoreBtn');
            const loadMoreContainer = document.getElementById('loadMoreContainer');
            
            if (currentlyShowing >= allHotelsData.length) {
                loadMoreContainer.style.display = 'none';
            } else {
                const remaining = allHotelsData.length - currentlyShowing;
                loadMoreBtn.innerHTML = `📋 Show ${Math.min(10, remaining)} More Hotels (${remaining} remaining)`;
            }
        }

        function displayHotels(hotels, cityName, source) {
            currentHotels = hotels;
            const hotelsList = document.getElementById('hotelsList');

            let html = '';
            hotels.forEach((hotel, index) => {
                const priceDisplay = hotel.price !== 'N/A' ? `€${hotel.price}/night` : 'Price on request';
                const stars = '⭐'.repeat(Math.floor(hotel.rating));
                
                // Determine source-specific styling
                const sourceClass = source === 'booking' ? 'source-booking' : 'source-tripadvisor';
                const bookBtnClass = source === 'booking' ? 'booking-source' : 'tripadvisor-source';
                const bookBtnText = source === 'booking' ? 'Book on Booking.com' : 'View on TripAdvisor';

                html += `
                    <div class="hotel-card ${sourceClass}" data-hotel-id="${hotel.id}" 
                         onmouseover="highlightMarker(${index})" 
                         onmouseout="unhighlightMarker(${index})">
                        <div class="hotel-name">${hotel.name}</div>
                        <div class="hotel-details">📍 ${hotel.address}</div>
                        ${hotel.room_type ? `<div class="room-type-display">${hotel.room_type}</div>` : ''}
                        <div class="price-info">
                            <span class="price">${priceDisplay}</span>
                            <span class="rating">${stars} ${hotel.rating}/5</span>
                        </div>
                        <div class="hotel-actions">
                            <a href="${hotel.booking_url}" target="_blank" class="action-btn book-btn ${bookBtnClass}">
                                ${bookBtnText}
                            </a>
                        </div>
                    </div>
                `;
            });

            hotelsList.innerHTML = html;
        }

        function updateMap(hotels) {
            currentMarkers.forEach(marker => map.removeLayer(marker));
            currentMarkers = [];

            if (hotels.length > 0) {
                const center = hotels[0].coordinates;
                map.setView(center, 12);

                hotels.forEach((hotel, index) => {
                    const marker = L.marker(hotel.coordinates)
                        .addTo(map)
                        .bindPopup(`
                            <b>${hotel.name}</b><br>
                            ${hotel.price !== 'N/A' ? `€${hotel.price}/night` : 'Price on request'}<br>
                            ⭐ ${hotel.rating}/5<br>
                            ${hotel.room_type ? `<em>${hotel.room_type}</em>` : ''}
                        `);

                    marker.on('click', () => highlightHotelCard(index));
                    currentMarkers.push(marker);
                });
            }
        }

        function highlightMarker(index) {
            if (currentMarkers[index]) {
                currentMarkers[index].openPopup();
            }
        }

        function unhighlightMarker(index) {
            if (currentMarkers[index]) {
                currentMarkers[index].closePopup();
            }
        }

        function highlightHotelCard(index) {
            document.querySelectorAll('.hotel-card').forEach(card => 
                card.classList.remove('highlighted'));

            const targetCard = document.querySelector(`[data-hotel-id="${currentHotels[index].id}"]`);
            if (targetCard) {
                targetCard.classList.add('highlighted');
                targetCard.scrollIntoView({behavior: 'smooth', block: 'center'});
            }
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', async function() {
            console.log('📄 Page loaded, waiting for Leaflet...');
            await waitForLeaflet();
            initializeApp();
        });
    </script>
</body>
</html>
