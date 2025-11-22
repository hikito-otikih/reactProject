import React, { useEffect, useState, useRef, useMemo } from 'react';

// --- HELPER FUNCTIONS ---
const SEGMENT_COLORS = [
  '#6366f1', '#ec4899', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6',
];

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
};

const formatTime = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
};

const addMinutesAndFormat = (dateString, minutes) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  date.setMinutes(date.getMinutes() + minutes);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
};

// --- COMPONENT ---
const RoutineMap = ({ onClose, routineData }) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [libLoaded, setLibLoaded] = useState(false);
  const [routeSegments, setRouteSegments] = useState([]);
  const [isLoadingRoute, setIsLoadingRoute] = useState(true);

  // --- 1. XỬ LÝ DATA (FIX LỖI INFINITE LOOP TẠI ĐÂY) ---
  // Gom tất cả việc trích xuất dữ liệu vào useMemo để đảm bảo path là ổn định (stable reference)
  const { path, total_duration_minutes, total_distance_km } = useMemo(() => {
    let data = routineData;
    
    // Parse nếu là string
    if (typeof routineData === 'string') {
      try {
        data = JSON.parse(routineData);
      } catch (error) {
        console.error("JSON Parse Error", error);
        data = null;
      }
    }

    // Trả về object chứa path đã được xử lý
    return {
      path: data?.path || [], 
      total_duration_minutes: data?.total_duration_minutes || 0,
      total_distance_km: data?.total_distance_km || 0
    };
  }, [routineData]); // Chỉ chạy lại khi routineData thay đổi từ cha

  // --- 2. Load Leaflet ---
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

// 3. Fetch Route Segments (Geoapify -> Fallback OSRM -> Fallback Straight Line)
  useEffect(() => {
    if (!path || path.length === 0) {
       setRouteSegments([]); 
       setIsLoadingRoute(false);
       return;
    }
    
    setIsLoadingRoute(true);
    
    const fetchRouteSegments = async () => {
      if (path.length < 2) {
        setIsLoadingRoute(false);
        return;
      }

      const apiKey = import.meta.env.VITE_GEOAPIFY_API_KEY; 
      const calculatedSegments = []; 

      // Loop tuần tự từng chặng
      for (let i = 0; i < path.length - 1; i++) {
          const start = path[i];
          const end = path[i+1];
          const color = SEGMENT_COLORS[i % SEGMENT_COLORS.length];
          
          let segmentCoords = null;

          // --- BƯỚC 1: THỬ GEOAPIFY (Ưu tiên) ---
          if (apiKey) {
            try {
                // Mẹo: Đổi 'motorcycle' thành 'drive' nếu đi xa, vì data xe máy đường dài thường hay bị lỗi tìm đường
                const mode = 'drive'; 
                const waypoints = `${start.lat},${start.lon}|${end.lat},${end.lon}`;
                const url = `https://api.geoapify.com/v1/routing?waypoints=${waypoints}&mode=${mode}&apiKey=${apiKey}`;
                
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    if (data.features && data.features.length > 0) {
                        const rawCoords = data.features[0].geometry.coordinates.flat();
                        segmentCoords = rawCoords.map(c => [c[1], c[0]]); // [lon, lat] -> [lat, lon]
                    }
                }
            } catch (err) {
                console.warn(`Geoapify failed for leg ${i}, trying OSRM...`);
            }
          }

          // --- BƯỚC 2: THỬ OSRM (Nếu Geoapify thất bại hoặc không có key) ---
          // OSRM là API mở, rất trâu bò cho đường dài
          if (!segmentCoords) {
             try {
                // Lưu ý: OSRM dùng format {lon},{lat}
                const url = `https://router.project-osrm.org/route/v1/driving/${start.lon},${start.lat};${end.lon},${end.lat}?overview=full&geometries=geojson`;
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    if (data.routes && data.routes.length > 0) {
                        const rawCoords = data.routes[0].geometry.coordinates;
                        segmentCoords = rawCoords.map(c => [c[1], c[0]]); // [lon, lat] -> [lat, lon]
                        console.log(`Leg ${i}: Retrieved via OSRM`);
                    }
                }
             } catch (err) {
                console.warn(`OSRM failed for leg ${i}`);
             }
          }

          // --- BƯỚC 3: FALLBACK CUỐI CÙNG (Vẽ đường thẳng) ---
          if (!segmentCoords) {
             segmentCoords = [[start.lat, start.lon], [end.lat, end.lon]];
             console.log(`Leg ${i}: Fallback to straight line`);
          }

          calculatedSegments.push({ positions: segmentCoords, color: color });

          // Delay nhẹ 200ms để tránh spam server (quan trọng cho Geoapify)
          if (apiKey) await new Promise(resolve => setTimeout(resolve, 200));
      }

      setRouteSegments(calculatedSegments);
      setIsLoadingRoute(false);
    };

    fetchRouteSegments();
  }, [path]);

  // --- 4. Initialize & Update Map ---
  useEffect(() => {
     if (!libLoaded || !mapContainerRef.current) return;

     // Init map
     if (!mapInstanceRef.current) {
       mapInstanceRef.current = window.L.map(mapContainerRef.current, {
         zoomControl: false,
         attributionControl: false
       }).setView([10.7739, 106.6977], 13);

       window.L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
         attribution: '&copy; OpenStreetMap'
       }).addTo(mapInstanceRef.current);
     }
     
     const map = mapInstanceRef.current;

     // Clean old layers
     map.eachLayer((layer) => {
        if (!layer._url) { map.removeLayer(layer); }
     });

     // Draw Polyline
     if (!isLoadingRoute) {
        routeSegments.forEach((segment, index) => {
           // Outer glow
           window.L.polyline(segment.positions, { color: segment.color, weight: 8, opacity: 0.3, lineCap: 'round' }).addTo(map);
           // Inner line
           const line = window.L.polyline(segment.positions, { color: segment.color, weight: 4, opacity: 1, lineCap: 'round', lineJoin: 'round' }).addTo(map);
           
           line.bindPopup(
             `<div class="text-xs font-bold text-gray-600 font-sans">Leg ${index + 1}: Stop ${index} ➝ Stop ${index + 1}</div>`,
             { closeButton: false, autoClose: false }
           );
        });
     }

     // Draw Markers
     if (path && path.length > 0) {
        const bounds = [];
        path.forEach((point) => {
           const latLng = [point.lat, point.lon];
           bounds.push(latLng);
           
           const bgColor = point.type === 'start' ? 'bg-violet-600' : 'bg-blue-500';
           const shadowColor = point.type === 'start' ? 'shadow-violet-500/50' : 'shadow-blue-500/50';
           
           const iconHtml = `
             <div class="relative flex flex-col items-center justify-center transform transition-all hover:scale-110 hover:-translate-y-1">
               <div class="w-10 h-10 ${bgColor} rounded-full flex items-center justify-center text-white font-bold text-sm border-4 border-white shadow-lg ${shadowColor}">
                 ${point.type === 'start' ? 'Start' : point.order}
               </div>
               <div class="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[8px] border-t-white -mt-[1px] filter drop-shadow-sm"></div>
             </div>
           `;

           const customIcon = window.L.divIcon({
             className: 'custom-marker-icon',
             html: iconHtml,
             iconSize: [40, 50],
             iconAnchor: [20, 50],
             popupAnchor: [0, -55]
           });

           const marker = window.L.marker(latLng, { icon: customIcon }).addTo(map);
           
           const headerGradient = point.type === 'start' ? 'bg-gradient-to-r from-violet-500 to-fuchsia-500' : 'bg-gradient-to-r from-blue-500 to-cyan-500';
           const popupContent = `
               <div class="overflow-hidden w-[240px] font-sans -m-5 rounded-lg shadow-lg bg-white">
                 <div class="h-20 p-4 flex items-end ${headerGradient}">
                     <h3 class="text-white font-bold text-lg leading-tight drop-shadow-md m-0">${point.name}</h3>
                 </div>
                 <div class="p-4 bg-white">
                     <div class="flex items-center justify-between mb-3">
                        <span class="text-xs font-semibold px-2 py-1 bg-gray-100 rounded text-gray-600 uppercase tracking-wider">
                          ${point.category}
                        </span>
                        ${point.rating ? `<span class="text-amber-500 font-bold text-xs">★ ${point.rating}</span>` : ''}
                     </div>
                     <p class="text-xs text-gray-500 mb-3 flex items-start gap-1">
                       <span class="opacity-70">📍</span>
                       ${point.address || 'Ho Chi Minh City'}
                     </p>
                     <div class="grid grid-cols-2 gap-2 border-t border-gray-100 pt-3">
                         <div class="text-center">
                             <p class="text-[10px] text-gray-400 uppercase m-0">Arrival</p>
                             <p class="font-bold text-gray-700 text-sm m-0">${formatTime(point.arrival_time)}</p>
                         </div>
                         <div class="text-center border-l border-gray-100">
                             <p class="text-[10px] text-gray-400 uppercase m-0">Stay</p>
                             <p class="font-bold text-gray-700 text-sm m-0">${point.visit_duration_minutes}m</p>
                         </div>
                     </div>
                 </div>
               </div>
           `;
           marker.bindPopup(popupContent, { className: 'custom-popup-wrapper', closeButton: false });
        });
        
        if (bounds.length > 0) {
           map.fitBounds(bounds, { padding: [80, 80], maxZoom: 15 });
        }
     }

  }, [libLoaded, isLoadingRoute, routeSegments, path]);

  // --- 5. Calculate Trip Details ---
  const tripDetails = useMemo(() => {
    if (!path || !path.length) return { date: 'N/A', timeRange: 'N/A', categories: [] };
    
    const startTime = path[0].arrival_time;
    const lastPoint = path[path.length - 1];
    const endTimeString = addMinutesAndFormat(lastPoint.arrival_time, lastPoint.visit_duration_minutes);
    const categories = [...new Set(path.map(p => p.category))].slice(0, 3);

    return {
      date: formatDate(startTime),
      timeRange: `${formatTime(startTime)} - ${endTimeString}`,
      categories
    };
  }, [path]);

  return (
     <div className="fixed inset-0 w-full h-full z-0 bg-gray-100 font-sans">
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 z-[1001] bg-white text-gray-800 p-2 rounded-full shadow-lg hover:bg-gray-100 transition-colors"
        >
           <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
        
        {/* Trip Info Card */}
        <div className="absolute top-6 left-6 z-[1000] animate-fadeIn max-w-xs w-full pointer-events-none">
           <div className="bg-white/90 backdrop-blur-md p-0 rounded-2xl shadow-2xl border border-white/20 overflow-hidden pointer-events-auto">
              <div className="bg-gradient-to-r from-indigo-600 to-blue-600 p-4">
                  <div className="flex items-center justify-between text-white">
                      <div>
                          <h2 className="text-lg font-bold flex items-center gap-2">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0121 18.382V7.618a1 1 0 01-1.447-.894L15 7m0 13V7"></path></svg>
                            Your Trip
                          </h2>
                          <p className="text-indigo-100 text-xs font-medium mt-0.5">{tripDetails.date}</p>
                      </div>
                      <div className="text-right">
                            <span className="bg-white/20 text-white text-xs px-2 py-1 rounded-lg font-bold backdrop-blur-sm border border-white/10">
                              {path.length} Stops
                            </span>
                      </div>
                  </div>
              </div>
              
              <div className="p-4 space-y-4">
                  <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                          </div>
                          <div>
                              <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Time Range</p>
                              <p className="text-sm font-bold text-gray-800">{tripDetails.timeRange}</p>
                          </div>
                      </div>
                      <div className="text-right">
                          <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Total</p>
                          <p className="text-sm font-bold text-gray-800">{(total_duration_minutes / 60).toFixed(1)} hrs</p>
                      </div>
                  </div>

                  <div className="flex items-center gap-2 border-t border-gray-100 pt-3">
                      <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                           <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                      </div>
                      <div className="flex-1">
                           <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Total Distance</p>
                           <p className="text-sm font-bold text-gray-800">{total_distance_km} km</p>
                      </div>
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                      {tripDetails.categories && tripDetails.categories.map((cat, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-600 border border-gray-200 capitalize">
                              {cat}
                          </span>
                      ))}
                  </div>
              </div>
           </div>
        </div>

        <div ref={mapContainerRef} className="w-full h-full outline-none bg-[#aad3df]" />
        
        <style>{`
          .custom-popup-wrapper .leaflet-popup-content-wrapper {
            padding: 0;
            border-radius: 0.5rem;
            background: transparent;
            box-shadow: none;
          }
          .custom-popup-wrapper .leaflet-popup-content {
            margin: 0;
          }
          .custom-popup-wrapper .leaflet-popup-tip {
            background: white;
          }
        `}</style>
     </div>
  );
};

export default RoutineMap;