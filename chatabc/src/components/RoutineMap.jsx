import React, { useEffect, useState, useRef } from 'react';
import { useAppContext } from '../context/AppContext';
import toast from 'react-hot-toast';
import axios from 'axios';

// --- COMPONENT ---
const RoutineMap = ({ showItinerary }) => {
  const { startPosition, setStartPosition, theme, selectedChat, token, schedulePlaces, setSchedulePlaces, showPreviewLocation, setShowPreviewLocation } = useAppContext();
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);
  const circleRef = useRef(null);
  const inputModeRef = useRef('name');
  const itineraryMarkersRef = useRef([]);
  const itineraryPolylineRef = useRef(null);
  const suggestionMarkerRef = useRef(null);
  const showItineraryRef = useRef(false);
  const previewMarkersRef = useRef([]);
  
  // Refs for State Synchronization (Fix Stale Closures)
  const selectedChatRef = useRef(null);
  const schedulePlacesRef = useRef([]); // <--- THÊM REF NÀY
  const routeModeRef = useRef('driving'); // <--- THÊM REF CHO ROUTE MODE
  
  const [libLoaded, setLibLoaded] = useState(false);
  const [mapReady, setMapReady] = useState(false);
  const [showPanel, setShowPanel] = useState(false);
  const [showInput, setShowInput] = useState(false);
  const [inputMode, setInputMode] = useState('name'); // 'name' | 'latlon' | 'click'
  const [searchName, setSearchName] = useState('');
  const [latInput, setLatInput] = useState('');
  const [lonInput, setLonInput] = useState('');
  const [searching, setSearching] = useState(false);
  const [clickedLocation, setClickedLocation] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestedPlaces, setSuggestedPlaces] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [routeMode, setRouteMode] = useState('driving'); // 'driving' | 'walking' | 'cycling'

  // Keep inputModeRef in sync with inputMode state
  useEffect(() => {
    inputModeRef.current = inputMode;
  }, [inputMode]);
  
  // Keep showItineraryRef in sync with showItinerary prop
  useEffect(() => {
    showItineraryRef.current = showItinerary;
  }, [showItinerary]);
  
  // Keep selectedChatRef in sync with selectedChat
  useEffect(() => {
    console.log('RoutineMap - selectedChat changed:', selectedChat);
    selectedChatRef.current = selectedChat;
  }, [selectedChat]);

  // --- THÊM: Keep schedulePlacesRef in sync with schedulePlaces ---
  useEffect(() => {
    // console.log('RoutineMap - schedulePlaces changed:', schedulePlaces);
    schedulePlacesRef.current = schedulePlaces;
  }, [schedulePlaces]);
  
  // Keep routeModeRef in sync with routeMode
  useEffect(() => {
    routeModeRef.current = routeMode;
  }, [routeMode]);

  // --- Load Leaflet ---
  useEffect(() => {
    if (window.L) {
      setLibLoaded(true);
      return;
    }
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);

    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.async = true;
    script.onload = () => setLibLoaded(true);
    document.body.appendChild(script);
  }, []);

  const updateStartPositionToDB = async (coordinate, name) => {
    // Use ref to get latest selectedChat value (fixes closure issue)
    const currentSelectedChat = selectedChatRef.current;
    
    // Check if selectedChat exists before updating DB
    if (!currentSelectedChat || !currentSelectedChat._id) {
      console.log('No chat selected, skipping start position DB update');
      return;
    }
    
    try {
      const response = await axios.post('/api/message/newStartPosition', {
        chatID: currentSelectedChat._id,
        start_coordinate: coordinate, // array of [lat, lon]
        start_coordinate_name: name // string
      }, {
        headers: {
          'Authorization': token
        }
      });
      console.log('Start position updated in DB:', response.data);
    } catch (error) {
      console.error('Failed to update start position in DB:', error);
    }
  };

  // --- Fetch route polyline from OpenStreetMap ---
  const fetchRoutePolyline = async (fromLat, fromLon, toLat, toLon, mode = 'driving') => {
    try {
      // Map mode to OSM routing profile
      const profileMap = {
        'driving': 'routed-car',
        'walking': 'routed-foot',
        'cycling': 'routed-bike'
      };
      
      const profile = profileMap[mode] || 'routed-car';
      
      const response = await fetch(
        `https://routing.openstreetmap.de/${profile}/route/v1/driving/${fromLon},${fromLat};${toLon},${toLat}?overview=full&geometries=geojson`
      );
      
      if (!response.ok) {
        console.warn(`OpenStreetMap ${mode} route failed:`, response.status);
        return null;
      }
      
      const data = await response.json();
      if (data && data.routes && data.routes.length > 0) {
        const coordinates = data.routes[0].geometry.coordinates;
        // OpenStreetMap returns [lon, lat], Leaflet needs [lat, lon]
        return coordinates.map(coord => [coord[1], coord[0]]);
      }
      
      return null;
    } catch (error) {
      console.warn(`Error fetching ${mode} route:`, error);
      return null;
    }
  };

  // --- Calculate driving distance using OpenStreetMap ---
  const calculateDrivingDistance = async (fromLat, fromLon, toLat, toLon) => {
    try {
      const response = await fetch(
        `https://routing.openstreetmap.de/routed-car/route/v1/driving/${fromLon},${fromLat};${toLon},${toLat}?overview=false`
      );
      
      if (!response.ok) {
        console.warn('OpenStreetMap directions failed:', response.status);
        return '0 km';
      }
      
      const data = await response.json();
      if (data && data.routes && data.routes.length > 0) {
        const distanceInMeters = data.routes[0].distance;
        const distanceInKm = distanceInMeters / 1000;
        
        if (distanceInKm < 1) {
          return `${Math.round(distanceInMeters)} m`;
        } else {
          return `${distanceInKm.toFixed(1)} km`;
        }
      }
      
      return '0 km';
    } catch (error) {
      console.warn('Error calculating driving distance:', error);
      return '0 km';
    }
  };

  // --- Handle map click for suggestions ---
  const handleMapClickForSuggestions = async (lat, lon) => {
    if (!mapInstanceRef.current) return;
    
    // Use ref to get latest selectedChat value
    const currentSelectedChat = selectedChatRef.current;
    
    // Check if selectedChat exists
    if (!currentSelectedChat || !currentSelectedChat._id) {
      console.error('selectedChat is null or missing _id:', currentSelectedChat);
      toast.error('Please select a chat first');
      return;
    }
    
    const map = mapInstanceRef.current;
    
    // Remove old suggestion marker if exists
    if (suggestionMarkerRef.current) {
      map.removeLayer(suggestionMarkerRef.current);
      suggestionMarkerRef.current = null;
    }
    
    // Add new marker at clicked location
    const clickIcon = window.L.divIcon({
      className: 'custom-click-marker',
      html: `
        <div class="w-8 h-8 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center text-white border-2 border-white shadow-xl animate-pulse">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
          </svg>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });
    
    const marker = window.L.marker([lat, lon], { icon: clickIcon }).addTo(map);
    suggestionMarkerRef.current = marker;
    
    // Set clicked location
    setClickedLocation({ lat, lon });
    setShowSuggestions(true);
    setLoadingSuggestions(true);
    
    console.log('Fetching suggestions for location:', { lat, lon, chatID: currentSelectedChat._id });
    
    try {
      // Call backend API
      const response = await axios.get('/api/message/getSuggestAround', {
        headers: { Authorization: token },
        params: { 
          lat, 
          lon, 
          chatID: currentSelectedChat._id 
        }
      });
      
      console.log('Fetched suggestions response:', response.data);
      
      if (!response.data || !response.data.suggestions || !response.data.suggestions.data) {
        throw new Error('Invalid response format');
      }
      // Helper function to safely parse lists
      const safeParseList = (str) => {
        if (!str) return [];
        try {
          const parsed = JSON.parse(str);
          return Array.isArray(parsed) ? parsed : [];
          } catch (e) {
            return [];
          }
        };

      const newresponse = await axios.post('/api/static_db/query', { list_id: response.data.suggestions.data });
      console.log('Processing suggestions data:', newresponse.data.data);
      
      // Determine reference point for distance calculation
      let refLat, refLon;
      
      // --- SỬA ĐỔI: Dùng Ref để lấy schedulePlaces mới nhất ---
      const currentSchedulePlaces = schedulePlacesRef.current;
      console.log('Current schedulePlaces (from Ref):', currentSchedulePlaces);

      if (currentSchedulePlaces && currentSchedulePlaces.length > 0) {
        // Use last place in itinerary
        const lastPlace = currentSchedulePlaces[currentSchedulePlaces.length - 1];
        refLat = parseFloat(lastPlace.Lat);
        refLon = parseFloat(lastPlace.Lon);
      } else if (startPosition) {
        // Use start position if no places in itinerary
        refLat = startPosition.lat;
        refLon = startPosition.lon;
      }
      
      // Map suggestions with temporary distance placeholder
      const tempSuggestions = newresponse.data.data.map((item, index) => {
        let parsedCategories = safeParseList(item.categories);
        if (parsedCategories.length === 0) parsedCategories = ["Place"];

        let parsedImages = safeParseList(item.images);
        
        let parsedReviews = [];
        try { if (item.reviews) parsedReviews = JSON.parse(item.reviews); } catch (e) {}
        
        let hoursObj = {};
        try { if (item.openingHours) hoursObj = JSON.parse(item.openingHours); } catch (e) {}

        const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
        const displayHours = hoursObj[today] || "Checking...";

        return {
          rowid: item.rowid,
          id: item.id || Date.now() + index,
          Name: item.name || item.title || item.address?.split(',')[0] || "Unknown",
          Address: item.address || "",
          Categories: parsedCategories,
          Image_URLs: parsedImages,
          Opening_Hours: displayHours,
          Rating: item.rating || 0,
          Phone: item.phone,
          Website: item.website,
          Description: item.description_en || item.description,
          Reviews: parsedReviews,
          Lat: item.location_lat || item.lat,
          Lon: item.location_lon || item.lon,
          distance: '0 km' // Will be updated
        };
      });
      
      // Calculate driving distances in parallel if reference point exists
      let finalSuggestions;
      if (refLat && refLon) {
        console.log('Calculating driving distances from reference point:', { refLat, refLon });
        
        // Use sequential processing to avoid rate limiting
        const calculatedSuggestions = [];
        for (const place of tempSuggestions) {
            const placeLat = parseFloat(place.Lat);
            const placeLon = parseFloat(place.Lon);
            
            if (!isNaN(placeLat) && !isNaN(placeLon)) {
                const distance = await calculateDrivingDistance(refLat, refLon, placeLat, placeLon);
                calculatedSuggestions.push({ ...place, distance });
            } else {
                calculatedSuggestions.push(place);
            }
            // Small delay to prevent rate limiting
            await new Promise(resolve => setTimeout(resolve, 300));
        }
        
        finalSuggestions = calculatedSuggestions;
        setSuggestedPlaces(finalSuggestions);
      } else {
        finalSuggestions = tempSuggestions;
        setSuggestedPlaces(tempSuggestions);
      }
      setLoadingSuggestions(false);
      toast.success(`Found ${finalSuggestions.length} nearby suggestions!`);
      
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setLoadingSuggestions(false);
      setSuggestedPlaces([]);
      toast.error('Failed to fetch suggestions. Please try again.');
    }
  };
  
  // --- Add suggested place to itinerary ---
  const handleAddSuggestedPlace = (place) => {
    const newPlace = {
      // rowid: null,
      id: Date.now(),
      ...place
    };

    // ✅ SỬ DỤNG FUNCTIONAL UPDATE
    // Cách này giúp bạn lấy được giá trị "prev" (cũ) chính xác nhất tại thời điểm chạy
    setSchedulePlaces(prevPlaces => {
      // 1. Tạo mảng mới dựa trên mảng cũ (prevPlaces)
      const updatedPlaces = [...prevPlaces, newPlace];
      
      // 2. CẬP NHẬT NGAY LẬP TỨC CHO REF (Quan trọng!)
      // Không cần chờ useEffect, ta ép Ref nhận giá trị mới luôn
      // Để các hàm async khác (như tính khoảng cách) dùng được ngay
      schedulePlacesRef.current = updatedPlaces; 

      const sortedRowIds = updatedPlaces.map((item) => item.rowid).filter(Boolean);
      if (sortedRowIds.length) {
        axios.post('/api/message/newSequence', {
          chatID: selectedChat?._id,
          sequence: sortedRowIds
        }, { headers: { Authorization: token} });
        console.log('Updated sequence sent to server:', sortedRowIds);
      }
      
      // console.log('Added place:', newPlace.Name);
      // console.log('Real-time Itinerary:', updatedPlaces);

      // 3. Trả về state mới cho React render
      return updatedPlaces;
    });

    toast.success(`Added "${place.Name}" to itinerary!`);
  };

  // --- Preview suggested place on map ---
  const handlePreviewSuggestedPlace = (place) => {
    if (!place || !place.Lat || !place.Lon) {
      toast.error('Location coordinates not available');
      return;
    }

    const previewLocation = {
      lat: parseFloat(place.Lat),
      lon: parseFloat(place.Lon),
      name: place.Name,
      address: place.Address,
      rating: place.Rating
    };

    setShowPreviewLocation([previewLocation]);
    toast.success('Location previewed on map!');
  };
  
  // --- Close suggestions panel ---
  const closeSuggestions = () => {
    setShowSuggestions(false);
    setSuggestedPlaces([]);
    setClickedLocation(null);
    
    if (suggestionMarkerRef.current && mapInstanceRef.current) {
      mapInstanceRef.current.removeLayer(suggestionMarkerRef.current);
      suggestionMarkerRef.current = null;
    }
  };

  // --- Search by name with LocationIQ ---
  const handleSearchByName = async () => {
    if (!searchName.trim()) {
      toast.error('Please enter a location name');
      return;
    }
    
    setSearching(true);
    
    try {
      const apiKeys = [
        import.meta.env.VITE_LOCATIONIQ_API_KEY,
        import.meta.env.VITE_LOCATIONIQ_API_KEY2,
        import.meta.env.VITE_LOCATIONIQ_API_KEY3,
        import.meta.env.VITE_LOCATIONIQ_API_KEY4
      ].filter(Boolean);
      
      if (apiKeys.length === 0) {
        console.error('LocationIQ API key not found in environment variables');
        toast.error('API key not configured');
        setSearching(false);
        return;
      }
      
      const apiKey = apiKeys[Math.floor(Math.random() * apiKeys.length)];
      
      const response = await fetch(
        `https://us1.locationiq.com/v1/search?key=${apiKey}&q=${encodeURIComponent(searchName)}&format=json&limit=1`
      );
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const data = await response.json();
      if (data && data.length > 0) {
        const location = data[0];
        setStartPosition({
          lat: parseFloat(location.lat),
          lon: parseFloat(location.lon),
          name: location.display_name
        });
        setShowInput(false);
        updateStartPositionToDB([parseFloat(location.lat), parseFloat(location.lon)], location.display_name);
        toast.success('Start position set!');
        setSearching(false);
        return;
      } else {
        toast.error('Location not found');
        setSearching(false);
      }
    } catch (error) {
      console.error('LocationIQ search failed:', error);
      toast.error('Failed to search location. Please try again.');
      setSearching(false);
    }
  };

  // --- Set by lat/lon ---
  const handleSetByLatLon = () => {
    const lat = parseFloat(latInput);
    const lon = parseFloat(lonInput);
    
    if (isNaN(lat) || isNaN(lon)) {
      toast.error('Invalid coordinates');
      return;
    }
    
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      toast.error('Coordinates out of range');
      return;
    }
    
    setStartPosition({
      lat,
      lon,
      name: `${lat.toFixed(4)}, ${lon.toFixed(4)}`
    });
    updateStartPositionToDB([lat, lon], `${lat.toFixed(4)}, ${lon.toFixed(4)}`);
    setShowInput(false);
    toast.success('Start position set!');
  };

  // --- Initialize Map ---
  useEffect(() => {
    if (!libLoaded || !mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = window.L.map(mapContainerRef.current, {
        zoomControl: true,
        attributionControl: false,
        worldCopyJump: true,
        maxBounds: [[-90, -180], [90, 180]]
      }).setView([10.7739, 106.6977], 13);

      // Use OpenStreetMap as base layer for better global coverage
      window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 2
      }).addTo(map);

      // Handle map click
      map.on('click', (e) => {
        if (inputModeRef.current === 'click') {
          // Otherwise handle normal click for start position
          setStartPosition({
            lat: e.latlng.lat,
            lon: e.latlng.lng,
            name: `${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`
          });
          updateStartPositionToDB([e.latlng.lat, e.latlng.lng], `${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`)
          setShowInput(false);
          setInputMode('name');
          toast.success('Start position set!');
        }
        // If in itinerary mode, show suggestions
        else if (showItineraryRef.current) {
          handleMapClickForSuggestions(e.latlng.lat, e.latlng.lng);
        }
        
      });

      mapInstanceRef.current = map;
      setMapReady(true);
    }
  }, [libLoaded]);

  // --- Update marker when startPosition changes ---
  useEffect(() => {
    if (!mapReady || !mapInstanceRef.current) return;

    const map = mapInstanceRef.current;

    // Always remove old marker and circle first
    if (markerRef.current) {
      map.removeLayer(markerRef.current);
      markerRef.current = null;
    }
    if (circleRef.current) {
      map.removeLayer(circleRef.current);
      circleRef.current = null;
    }

    // Remove any stray circles (cleanup for animation issues)
    map.eachLayer((layer) => {
      if (layer instanceof window.L.Circle && layer.options.className === 'pulsing-circle') {
        map.removeLayer(layer);
      }
    });

    // If no startPosition, just return after cleanup
    if (!startPosition) return;

    // Add pulsing circle
    const circle = window.L.circle([startPosition.lat, startPosition.lon], {
      color: '#8b5cf6',
      fillColor: '#8b5cf6',
      fillOpacity: 0.2,
      radius: 500
    }).addTo(map);
    circleRef.current = circle;

    // Add special marker
    const iconHtml = `
      <div class="relative flex flex-col items-center justify-center animate-bounce-slow">
        <div class="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg border-4 border-white shadow-2xl shadow-violet-500/50 animate-pulse-slow">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
          </svg>
        </div>
        <div class="w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-t-[12px] border-t-white -mt-[2px] filter drop-shadow-lg"></div>
      </div>
    `;

    const customIcon = window.L.divIcon({
      className: 'custom-start-marker',
      html: iconHtml,
      iconSize: [48, 60],
      iconAnchor: [24, 60],
      popupAnchor: [0, -65]
    });

    const marker = window.L.marker([startPosition.lat, startPosition.lon], { 
      icon: customIcon 
    }).addTo(map);
    
    marker.bindPopup(
      `<div class="text-sm font-bold text-violet-600">Start Position</div><div class="text-xs text-gray-600">${startPosition.name}</div>`,
      { className: 'custom-popup-wrapper', closeButton: false }
    );
    
    markerRef.current = marker;

    // Center map on marker
    map.setView([startPosition.lat, startPosition.lon], 14, { animate: true });

  }, [mapReady, startPosition]);

  // --- Display Itinerary on Map ---
  useEffect(() => {
    if (!mapReady || !mapInstanceRef.current) return;
    
    const map = mapInstanceRef.current;
    
    // ALWAYS clear existing itinerary markers and polylines first
    itineraryMarkersRef.current.forEach(marker => {
      try {
        map.removeLayer(marker);
      } catch (e) {
        // Marker might already be removed
      }
    });
    itineraryMarkersRef.current = [];
    
    if (itineraryPolylineRef.current) {
      try {
        map.removeLayer(itineraryPolylineRef.current);
      } catch (e) {
        // Polyline might already be removed
      }
      itineraryPolylineRef.current = null;
    }
    
    // If showItinerary is false or no places, STOP HERE (cleanup done)
    if (!showItinerary || !schedulePlaces || schedulePlaces.length === 0) {
      return;
    }
    //console.log('Displaying itinerary on map with places:', schedulePlaces);
    //console.log('displaying itinerary on map with places ref:', schedulePlacesRef.current);
    // Collect all coordinates (start position + all places)
    const allCoordinates = [];
    
    // Add start position if exists
    if (startPosition) {
      allCoordinates.push([startPosition.lat, startPosition.lon]);
    }
    
    // Add all place coordinates
    schedulePlaces.forEach((place, index) => {
      // Use Lat and Lon fields directly from place data
      const lat = parseFloat(place.Lat);
      const lon = parseFloat(place.Lon);
      //console.log(`Place ${index + 1}:`, place.Name, lat, lon);
      // If coordinates are valid, add marker
      if (!isNaN(lat) && !isNaN(lon) && 
          lat >= -90 && lat <= 90 && 
          lon >= -180 && lon <= 180) {
        allCoordinates.push([lat, lon]);
        
        // Create numbered marker for each place
        const numberIcon = window.L.divIcon({
          className: 'custom-number-marker',
          html: `
            <div class="relative flex items-center justify-center">
              <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm border-3 border-white shadow-xl">
                ${index + 1}
              </div>
            </div>
          `,
          iconSize: [40, 40],
          iconAnchor: [20, 20],
          popupAnchor: [0, -20]
        });
        
        const marker = window.L.marker([lat, lon], { icon: numberIcon }).addTo(map);
        // Build detailed popup content
        const categories = Array.isArray(place.Categories) ? place.Categories.slice(0, 3).join(', ') : '';
        const rating = place.Rating || 0;
        const stars = '⭐'.repeat(Math.floor(rating));
        const imageUrl = Array.isArray(place.Image_URLs) && place.Image_URLs.length > 0 ? place.Image_URLs[0] : '';
        const description = place.Description ? (place.Description.length > 100 ? place.Description.substring(0, 100) + '...' : place.Description) : '';
        const hours = place.Opening_Hours || 'N/A';
        
        const popupContent = `
          <div class="itinerary-popup" style="min-width: 280px; max-width: 320px;">
            ${imageUrl ? `
              <div class="popup-image-container" style="width: 100%; height: 140px; overflow: hidden; border-radius: 8px 8px 0 0; margin: -12px -16px 12px -16px;">
                <img src="${imageUrl}" 
                     alt="${place.Name}" 
                     referrerpolicy="no-referrer"
                     style="width: 100%; height: 100%; object-fit: cover;"
                     onerror="this.parentElement.style.display='none'"/>
              </div>
            ` : ''}
            
            <div class="popup-header" style="margin-bottom: 8px;">
              <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                <span style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border-radius: 50%; font-weight: bold; font-size: 12px; flex-shrink: 0;">
                  ${index + 1}
                </span>
                <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #1e40af; line-height: 1.3;">
                  ${place.Name}
                </h3>
              </div>
              
              ${rating > 0 ? `
                <div style="display: flex; align-items: center; gap: 6px; margin-top: 6px;">
                  <span style="font-size: 14px; line-height: 1;">${stars}</span>
                  <span style="font-weight: 600; color: #1f2937; font-size: 13px;">${rating.toFixed(1)}</span>
                </div>
              ` : ''}
              
              ${categories ? `
                <div style="margin-top: 6px;">
                  <div style="display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; background: #dbeafe; border-radius: 12px; font-size: 11px; color: #1e40af; font-weight: 600;">
                    <svg style="width: 12px; height: 12px;" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
                    </svg>
                    ${categories}
                  </div>
                </div>
              ` : ''}
            </div>
            
            ${description ? `
              <div style="margin: 10px 0; padding: 8px; background: #f9fafb; border-radius: 6px; border-left: 3px solid #3b82f6;">
                <p style="margin: 0; font-size: 12px; color: #4b5563; line-height: 1.5;">
                  ${description}
                </p>
              </div>
            ` : ''}
            
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #e5e7eb;">
              <div style="display: flex; align-items: start; gap: 6px; margin-bottom: 6px;">
                <svg style="width: 14px; height: 14px; color: #6b7280; margin-top: 1px; flex-shrink: 0;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                <span style="font-size: 11px; color: #6b7280; line-height: 1.4;">
                  ${place.Address}
                </span>
              </div>
              
              <div style="display: flex; align-items: center; gap: 6px;">
                <svg style="width: 14px; height: 14px; color: #6b7280; flex-shrink: 0;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span style="font-size: 11px; color: ${hours.includes('Open') || hours.includes('Mở') ? '#059669' : hours.includes('Closed') || hours.includes('Đóng') ? '#dc2626' : '#6b7280'}; font-weight: 600;">
                  ${hours}
                </span>
              </div>
              
              ${place.Phone ? `
                <div style="display: flex; align-items: center; gap: 6px; margin-top: 6px;">
                  <svg style="width: 14px; height: 14px; color: #6b7280; flex-shrink: 0;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
                  </svg>
                  <a href="tel:${place.Phone}" style="font-size: 11px; color: #3b82f6; text-decoration: none; font-weight: 500;">
                    ${place.Phone}
                  </a>
                </div>
              ` : ''}
              
              ${place.Website ? `
                <div style="display: flex; align-items: center; gap: 6px; margin-top: 6px;">
                  <svg style="width: 14px; height: 14px; color: #6b7280; flex-shrink: 0;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
                  </svg>
                  <a href="${place.Website}" target="_blank" style="font-size: 11px; color: #3b82f6; text-decoration: none; font-weight: 500;">
                    Visit Website
                  </a>
                </div>
              ` : ''}
            </div>
          </div>
        `;
        
        marker.bindPopup(popupContent, { 
          className: 'custom-itinerary-popup',
          closeButton: true,
          maxWidth: 340,
          minWidth: 280
        });
        
        itineraryMarkersRef.current.push(marker);
      }
    });
    
    // Draw polyline connecting all points using LocationIQ routes
    let isCancelled = false;
    
    const drawRoutes = async () => {
      if (allCoordinates.length > 1) {
        const allRoutePoints = [];
        const currentRouteMode = routeModeRef.current;
        
        // Fetch routes sequentially between each pair of points
        for (let i = 0; i < allCoordinates.length - 1; i++) {
          // Check if effect was cancelled or route mode changed
          if (isCancelled || currentRouteMode !== routeModeRef.current) {
            console.log('Route drawing cancelled or mode changed');
            return;
          }
          
          const [fromLat, fromLon] = allCoordinates[i];
          const [toLat, toLon] = allCoordinates[i + 1];
          
          const routePoints = await fetchRoutePolyline(fromLat, fromLon, toLat, toLon, currentRouteMode);
          
          if (routePoints && routePoints.length > 0) {
            // Add route points (avoid duplicating connection points)
            if (i === 0) {
              allRoutePoints.push(...routePoints);
            } else {
              // Skip first point to avoid duplicate
              allRoutePoints.push(...routePoints.slice(1));
            }
          } else {
            // Fallback to straight line if API fails
            if (i === 0) {
              allRoutePoints.push([fromLat, fromLon]);
            }
            allRoutePoints.push([toLat, toLon]);
          }
          
          // Small delay to avoid rate limiting
          await new Promise(resolve => setTimeout(resolve, 300));
        }
        
        // Check one more time before drawing
        if (isCancelled || currentRouteMode !== routeModeRef.current) {
          console.log('Route drawing cancelled before polyline creation');
          return;
        }
        
        // Draw the complete route
        if (allRoutePoints.length > 0) {
          const polyline = window.L.polyline(allRoutePoints, {
            color: currentRouteMode === 'driving' ? 'blue' : currentRouteMode === 'walking' ? 'green' : 'orange',
            weight: 4,
            opacity: 0.7,
            smoothFactor: 1
          }).addTo(map);
          
          itineraryPolylineRef.current = polyline;
          
          // Fit map bounds to show entire route
          map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
        }
      }
    };
    
    // Call async function
    drawRoutes();
    
    // Cleanup function to cancel ongoing route drawing
    return () => {
      isCancelled = true;
      // Clear any routes that might be in progress
      itineraryMarkersRef.current.forEach(marker => {
        try {
          map.removeLayer(marker);
        } catch (e) {}
      });
      itineraryMarkersRef.current = [];
      
      if (itineraryPolylineRef.current) {
        try {
          map.removeLayer(itineraryPolylineRef.current);
        } catch (e) {}
        itineraryPolylineRef.current = null;
      }
    };
    
  }, [mapReady, showItinerary, schedulePlaces, startPosition, routeMode]);

  // --- Display Preview Locations on Map ---
  useEffect(() => {
    if (!mapReady || !window.L || !mapInstanceRef.current) return;

    const L = window.L;
    const map = mapInstanceRef.current;

    // Clear existing preview markers
    previewMarkersRef.current.forEach(marker => marker.remove());
    previewMarkersRef.current = [];

    // Add new preview markers
    if (showPreviewLocation && showPreviewLocation.length > 0) {
      showPreviewLocation.forEach((location) => {
        const { lat, lon, name, address, rating } = location;

        // Create custom green icon for preview
        const greenIcon = L.divIcon({
          className: 'custom-marker-preview',
          html: `
            <div style="position: relative; width: 40px; height: 40px;">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="#10b981" stroke="white" stroke-width="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                <circle cx="12" cy="10" r="3"></circle>
              </svg>
            </div>
          `,
          iconSize: [40, 40],
          iconAnchor: [20, 40],
          popupAnchor: [0, -40]
        });

        const marker = L.marker([lat, lon], { icon: greenIcon }).addTo(map);

        // Create popup content
        let popupContent = `
          <div style="min-width: 200px; font-family: sans-serif;">
            <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold; color: #1f2937;">${name}</h3>
            ${address ? `<p style="margin: 4px 0; font-size: 13px; color: #6b7280;">${address}</p>` : ''}
            ${rating ? `
              <div style="display: flex; align-items: center; gap: 4px; margin-top: 6px;">
                <svg width="14" height="14" fill="#fbbf24" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                </svg>
                <span style="font-size: 13px; font-weight: 600; color: #1f2937;">${rating}</span>
              </div>
            ` : ''}
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #e5e7eb;">
              <span style="font-size: 12px; color: #10b981; font-weight: 600;">📍 Preview Location</span>
            </div>
          </div>
        `;

        marker.bindPopup(popupContent);
        marker.openPopup();

        previewMarkersRef.current.push(marker);
      });

      // Fit map to show all preview locations
      if (showPreviewLocation.length > 0) {
        const bounds = L.latLngBounds(showPreviewLocation.map(loc => [loc.lat, loc.lon]));
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
      }
    }
  }, [mapReady, showPreviewLocation]);

  // --- Auto Resize Handler ---
  useEffect(() => {
    if (!mapReady || !mapContainerRef.current || !mapInstanceRef.current) return;

    const map = mapInstanceRef.current;
    const resizeObserver = new ResizeObserver(() => {
      map.invalidateSize();
    });

    resizeObserver.observe(mapContainerRef.current);
    return () => resizeObserver.disconnect();
  }, [mapReady]);

  return (
    <div className="w-full h-full relative z-0 bg-gray-100 font-sans">
      {/* Close button */}
      {/* <button 
        onClick={onClose}
        className="absolute top-6 right-6 z-[1001] bg-white text-gray-800 p-2 rounded-full shadow-lg hover:bg-gray-100 transition-colors"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button> */}

      {/* Route Mode Tabs - Show only when itinerary is displayed */}
      {showItinerary && (
        <div className="absolute top-6 left-1/2 transform -translate-x-1/2 z-[1001] animate-slideInRight">
          <div className={`flex gap-1 p-1 rounded-full shadow-lg backdrop-blur-md ${
            theme === 'dark' ? 'bg-slate-800/95' : 'bg-white/95'
          }`}>
            <button
              onClick={() => setRouteMode('driving')}
              className={`px-4 py-2 rounded-full text-xs font-semibold transition-all flex items-center gap-1.5 ${
                routeMode === 'driving'
                  ? 'bg-blue-500 text-white shadow-md'
                  : theme === 'dark'
                  ? 'text-gray-300 hover:bg-slate-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z"/>
                <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707l-2-2A1 1 0 0015 7h-1z"/>
              </svg>
              Driving
            </button>
            <button
              onClick={() => setRouteMode('walking')}
              className={`px-4 py-2 rounded-full text-xs font-semibold transition-all flex items-center gap-1.5 ${
                routeMode === 'walking'
                  ? 'bg-green-500 text-white shadow-md'
                  : theme === 'dark'
                  ? 'text-gray-300 hover:bg-slate-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
              </svg>
              Walking
            </button>
            <button
              onClick={() => setRouteMode('cycling')}
              className={`px-4 py-2 rounded-full text-xs font-semibold transition-all flex items-center gap-1.5 ${
                routeMode === 'cycling'
                  ? 'bg-amber-500 text-white shadow-md'
                  : theme === 'dark'
                  ? 'text-gray-300 hover:bg-slate-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M3.5 14.5a3 3 0 100-6 3 3 0 000 6zM16.5 14.5a3 3 0 100-6 3 3 0 000 6z"/>
                <path d="M7 10l2-4h2l2 4M9 10h2"/>
              </svg>
              Cycling
            </button>
          </div>
        </div>
      )}

      {/* Toggle Panel Button */}
      <button
        onClick={() => setShowPanel(!showPanel)}
        className={`absolute top-6 left-10 z-[1001] shadow-lg transition-all flex items-center gap-2 ${
          showPanel
            ? 'bg-red-500 hover:bg-red-600 text-white p-2.5 rounded-full'
            : 'bg-violet-600 hover:bg-violet-700 text-white px-3 py-2.5 rounded-full'
        }`}
        title={showPanel ? 'Close Panel' : 'Set Start Position'}
      >
        {showPanel ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        ) : (
          <>
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd"/>
            </svg>
            <span className="text-sm font-semibold">Start Position</span>
          </>
        )}
      </button>

      {/* Start Position Info Panel - Popup */}
      {showPanel && (
      <div className="absolute top-20 left-6 z-[1000] w-80 animate-slideInLeft">
        <div className={`rounded-xl shadow-2xl border overflow-hidden backdrop-blur-md ${
          theme === 'dark' 
            ? 'bg-slate-800/95 border-slate-700' 
            : 'bg-white/95 border-white/20'
        }`}>
          {/* Header */}
          <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-3">
            <div className="flex items-center justify-between text-white">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd"/>
                </svg>
                <h2 className="text-sm font-bold">Start Position</h2>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-3 space-y-2">
            {startPosition ? (
              <>
                <div className={`p-2 rounded-lg ${
                  theme === 'dark' ? 'bg-slate-700/50' : 'bg-violet-50'
                }`}>
                  <p className="text-[10px] text-violet-600 dark:text-violet-400 font-semibold mb-0.5">Current Location</p>
                  <p className={`text-xs font-bold line-clamp-2 ${
                    theme === 'dark' ? 'text-gray-100' : 'text-gray-800'
                  }`}>{startPosition.name}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">
                    {startPosition.lat.toFixed(4)}, {startPosition.lon.toFixed(4)}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setStartPosition(null);
                    updateStartPositionToDB(null, null);
                    setShowInput(true);
                  }}
                  className="w-full px-2 py-1.5 text-xs font-semibold rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors"
                >
                  Clear & Set New
                </button>
              </>
            ) : (
              <>
                <div className={`p-2 rounded-lg border-2 border-dashed ${
                  theme === 'dark' 
                    ? 'border-slate-600 bg-slate-700/30' 
                    : 'border-gray-300 bg-gray-50'
                }`}>
                  <p className={`text-xs text-center ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    No start position set
                  </p>
                </div>
                
                {!showInput && (
                  <button
                    onClick={() => setShowInput(true)}
                    className="w-full px-2 py-1.5 text-xs font-semibold rounded-lg bg-violet-600 text-white hover:bg-violet-700 transition-colors flex items-center justify-center gap-1.5"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/>
                    </svg>
                    Set Start Position
                  </button>
                )}

                {showInput && (
                  <div className="space-y-2">
                    {/* Input Mode Tabs */}
                    <div className="flex gap-0.5 p-0.5 bg-gray-200 dark:bg-slate-700 rounded-lg">
                      <button
                        onClick={() => setInputMode('name')}
                        className={`flex-1 px-1.5 py-1 text-[10px] font-semibold rounded transition-colors ${
                          inputMode === 'name'
                            ? 'bg-white dark:bg-slate-600 text-violet-600 shadow-sm'
                            : 'text-gray-600 dark:text-gray-400'
                        }`}
                      >
                        Name
                      </button>
                      <button
                        onClick={() => setInputMode('latlon')}
                        className={`flex-1 px-1.5 py-1 text-[10px] font-semibold rounded transition-colors ${
                          inputMode === 'latlon'
                            ? 'bg-white dark:bg-slate-600 text-violet-600 shadow-sm'
                            : 'text-gray-600 dark:text-gray-400'
                        }`}
                      >
                        Lat/Lon
                      </button>
                      <button
                        onClick={() => setInputMode('click')}
                        className={`flex-1 px-1.5 py-1 text-[10px] font-semibold rounded transition-colors ${
                          inputMode === 'click'
                            ? 'bg-white dark:bg-slate-600 text-violet-600 shadow-sm'
                            : 'text-gray-600 dark:text-gray-400'
                        }`}
                      >
                        Click
                      </button>
                    </div>

                    {/* Input by Name */}
                    {inputMode === 'name' && (
                      <div className="space-y-1.5">
                        <input
                          type="text"
                          value={searchName}
                          onChange={(e) => setSearchName(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && handleSearchByName()}
                          placeholder="Enter location..."
                          className={`w-full px-2 py-1.5 text-xs rounded-lg border ${
                            theme === 'dark'
                              ? 'bg-slate-700 border-slate-600 text-gray-100'
                              : 'bg-white border-gray-300 text-gray-800'
                          }`}
                        />
                        <button
                          onClick={handleSearchByName}
                          disabled={searching}
                          className="w-full px-2 py-1.5 text-xs font-semibold rounded-lg bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50 transition-colors"
                        >
                          {searching ? 'Searching...' : 'Search'}
                        </button>
                      </div>
                    )}

                    {/* Input by Lat/Lon */}
                    {inputMode === 'latlon' && (
                      <div className="space-y-1.5">
                        <input
                          type="number"
                          step="0.0001"
                          value={latInput}
                          onChange={(e) => setLatInput(e.target.value)}
                          placeholder="Latitude"
                          className={`w-full px-2 py-1.5 text-xs rounded-lg border ${
                            theme === 'dark'
                              ? 'bg-slate-700 border-slate-600 text-gray-100'
                              : 'bg-white border-gray-300 text-gray-800'
                          }`}
                        />
                        <input
                          type="number"
                          step="0.0001"
                          value={lonInput}
                          onChange={(e) => setLonInput(e.target.value)}
                          placeholder="Longitude"
                          className={`w-full px-2 py-1.5 text-xs rounded-lg border ${
                            theme === 'dark'
                              ? 'bg-slate-700 border-slate-600 text-gray-100'
                              : 'bg-white border-gray-300 text-gray-800'
                          }`}
                        />
                        <button
                          onClick={handleSetByLatLon}
                          className="w-full px-2 py-1.5 text-xs font-semibold rounded-lg bg-violet-600 text-white hover:bg-violet-700 transition-colors"
                        >
                          Set Position
                        </button>
                      </div>
                    )}

                    {/* Click Map Mode */}
                    {inputMode === 'click' && (
                      <div className={`p-2 rounded-lg border-2 border-dashed border-violet-400 ${
                        theme === 'dark' ? 'bg-violet-900/20' : 'bg-violet-50'
                      }`}>
                        <p className="text-[10px] text-violet-600 dark:text-violet-400 text-center font-semibold">
                          👆 Click on map
                        </p>
                      </div>
                    )}

                    <button
                      onClick={() => {
                        setShowInput(false);
                        setInputMode('name');
                      }}
                      className={`w-full px-2 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                        theme === 'dark'
                          ? 'border-slate-600 text-gray-300 hover:bg-slate-700'
                          : 'border-gray-300 text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
      )}

      {/* Suggestions Panel */}
      {showSuggestions && (
        <div className="absolute top-20 right-6 z-[1000] w-96 max-h-[calc(100vh-140px)] animate-slideInRight">
          <div className={`rounded-xl shadow-2xl border overflow-hidden backdrop-blur-md ${
            theme === 'dark' 
              ? 'bg-slate-800/95 border-slate-700' 
              : 'bg-white/95 border-white/20'
          }`}>
            {/* Header */}
            <div className="bg-gradient-to-r from-orange-500 to-red-500 p-4">
              <div className="flex items-center justify-between text-white">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd"/>
                  </svg>
                  <h2 className="text-sm font-bold">Nearby Suggestions</h2>
                </div>
                <button
                  onClick={closeSuggestions}
                  className="p-1 hover:bg-white/20 rounded-full transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
              {clickedLocation && (
                <p className="text-xs text-white/80 mt-1">
                  📍 {clickedLocation.lat.toFixed(4)}, {clickedLocation.lon.toFixed(4)}
                </p>
              )}
            </div>

            {/* Content */}
            <div className="overflow-y-auto max-h-[calc(100vh-220px)] custom-scrollbar">
              {loadingSuggestions ? (
                <div className="flex flex-col items-center justify-center p-8 gap-3">
                  <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin"></div>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                    Finding nearby places...
                  </p>
                </div>
              ) : suggestedPlaces.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 gap-2">
                  <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                    No suggestions found
                  </p>
                </div>
              ) : (
                <div className="p-3 space-y-3">
                  {suggestedPlaces.map((place, index) => {
                    const imageUrl = Array.isArray(place.Image_URLs) && place.Image_URLs.length > 0 ? place.Image_URLs[0] : '';
                    const categories = Array.isArray(place.Categories) ? place.Categories.slice(0, 2).join(', ') : '';
                    const rating = place.Rating || 0;
                    
                    return (
                      <div
                        key={place.id}
                        className={`rounded-lg border overflow-hidden transition-all hover:shadow-lg hover:scale-[1.02] ${
                          theme === 'dark' 
                            ? 'bg-slate-700/50 border-slate-600 hover:border-orange-500' 
                            : 'bg-white border-gray-200 hover:border-orange-400'
                        }`}
                      >
                        {imageUrl && (
                          <div className="h-32 overflow-hidden">
                            <img
                              src={imageUrl}
                              alt={place.Name}
                              referrerPolicy="no-referrer"
                              className="w-full h-full object-cover"
                              onError={(e) => e.target.parentElement.style.display = 'none'}
                            />
                          </div>
                        )}
                        
                        <div className="p-3">
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <h3 className={`font-bold text-sm line-clamp-1 ${
                              theme === 'dark' ? 'text-gray-100' : 'text-gray-900'
                            }`}>
                              {place.Name}
                            </h3>
                            {place.distance && (
                              <span className="text-xs font-semibold text-orange-500 whitespace-nowrap">
                                {place.distance}
                              </span>
                            )}
                          </div>
                          
                          {rating > 0 && (
                            <div className="flex items-center gap-1 mb-2">
                              <span className="text-yellow-400 text-sm">{'⭐'.repeat(Math.floor(rating))}</span>
                              <span className="text-xs font-semibold text-gray-600 dark:text-gray-400">
                                {rating.toFixed(1)}
                              </span>
                            </div>
                          )}
                          
                          {categories && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                              🏷️ {categories}
                            </p>
                          )}
                          
                          {place.Description && (
                            <p className={`text-xs line-clamp-2 mb-3 ${
                              theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                            }`}>
                              {place.Description}
                            </p>
                          )}
                          
                          <button
                            onClick={() => handleAddSuggestedPlace(place)}
                            className="w-full px-3 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold text-sm hover:from-orange-600 hover:to-red-600 transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/>
                            </svg>
                            Add to Itinerary
                          </button>

                          <button
                            onClick={() => handlePreviewSuggestedPlace(place)}
                            className="w-full px-3 py-2 rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold text-sm hover:from-green-600 hover:to-emerald-700 transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg mt-2"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"/>
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"/>
                            </svg>
                            Preview on Map
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Map Container */}
      <div ref={mapContainerRef} className="w-full h-full outline-none bg-[#aad3df]" />
      
      {/* Styles */}
      <style>{`
        .custom-popup-wrapper .leaflet-popup-content-wrapper { 
          padding: 8px; 
          border-radius: 0.5rem; 
          background: white; 
          box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        }
        .custom-popup-wrapper .leaflet-popup-content { margin: 0; }
        .custom-popup-wrapper .leaflet-popup-tip { background: white; }
        
        .custom-itinerary-popup .leaflet-popup-content-wrapper {
          padding: 12px 16px;
          border-radius: 12px;
          background: white;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15), 0 4px 10px rgba(0, 0, 0, 0.1);
          border: 1px solid #e5e7eb;
        }
        
        .custom-itinerary-popup .leaflet-popup-content {
          margin: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }
        
        .custom-itinerary-popup .leaflet-popup-tip {
          background: white;
          border: 1px solid #e5e7eb;
        }
        
        .custom-itinerary-popup .leaflet-popup-close-button {
          color: #6b7280 !important;
          font-size: 20px !important;
          padding: 4px 8px !important;
          width: auto !important;
          height: auto !important;
          transition: color 0.2s;
        }
        
        .custom-itinerary-popup .leaflet-popup-close-button:hover {
          color: #1f2937 !important;
          background: transparent !important;
        }
        
        .itinerary-popup h3 {
          word-wrap: break-word;
          overflow-wrap: break-word;
        }
        
        .itinerary-popup a:hover {
          text-decoration: underline;
        }
        
        @keyframes pulse-slow {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.05); }
        }
        
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        
        .animate-pulse-slow {
          animation: pulse-slow 2s ease-in-out infinite;
        }
        
        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
        
        .pulsing-circle {
          animation: pulse-slow 2s ease-in-out infinite;
        }
        
        .custom-start-marker {
          filter: drop-shadow(0 10px 15px rgba(139, 92, 246, 0.4));
        }
        
        .custom-number-marker {
          filter: drop-shadow(0 4px 6px rgba(59, 130, 246, 0.5));
          transition: transform 0.2s ease;
        }
        
        .custom-number-marker:hover {
          transform: scale(1.1);
          filter: drop-shadow(0 6px 10px rgba(59, 130, 246, 0.7));
        }
        
        .custom-click-marker {
          background: transparent !important;
          border: none !important;
          filter: drop-shadow(0 4px 8px rgba(249, 115, 22, 0.6));
        }
        
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .leaflet-control-zoom {
          border: none !important;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        }
        
        .leaflet-control-zoom a {
          background-color: white !important;
          color: #374151 !important;
          border: none !important;
        }
        
        .leaflet-control-zoom a:hover {
          background-color: #f3f4f6 !important;
        }
        
        @keyframes slideInLeft {
          0% { opacity: 0; transform: translateX(-20px); }
          100% { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes slideInRight {
          0% { opacity: 0; transform: translateX(20px); }
          100% { opacity: 1; transform: translateX(0); }
        }
        
        .animate-slideInLeft {
          animation: slideInLeft 0.3s ease-out;
        }
        
        .animate-slideInRight {
          animation: slideInRight 0.3s ease-out;
        }
        
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-track {
          background: ${theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'};
          border-radius: 4px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: ${theme === 'dark' ? '#4b5563' : '#cbd5e1'};
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
};

export default RoutineMap;