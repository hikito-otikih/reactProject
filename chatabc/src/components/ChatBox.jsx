import React, { useEffect, useRef, useState } from 'react'
import { useAppContext } from '../context/AppContext'
import { assets } from '../assets/assets';
import Message from './Message';
import toast from 'react-hot-toast';
import { Compass, Map, Coffee, Music } from 'lucide-react';

// --- COMPONENT MÀN HÌNH CHỜ (RELAXING SCREEN) ---
const EmptyState = ({ setPrompt }) => {
  const suggestions = [
    { icon: <Map size={20} />, text: "Lên lịch trình đi Đà Lạt 3 ngày 2 đêm", label: "Trip Planning" },
    { icon: <Coffee size={20} />, text: "Tìm quán cafe yên tĩnh ở Quận 1", label: "Relaxing" },
    { icon: <Compass size={20} />, text: "Gợi ý địa điểm du lịch gần Sài Gòn", label: "Explore" },
    { icon: <Music size={20} />, text: "Địa điểm nghe nhạc Acoustic tối nay", label: "Entertainment" },
  ];

  return (
    <div className="h-full flex flex-col items-center justify-center animate-fadeIn p-4">
      {/* Logo & Greeting */}
      <div className="flex flex-col items-center mb-10 space-y-4">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-500 blur-2xl opacity-20 rounded-full animate-pulse"></div>
          <img 
            src={assets.gemini_icon} 
            alt="AI Logo" 
            className="w-16 h-16 md:w-20 md:h-20 object-contain relative z-10 drop-shadow-lg"
          />
        </div>
        <h2 className="text-2xl md:text-3xl font-bold text-gray-700 dark:text-gray-200 text-center">
          Hi, Traveler! 👋
        </h2>
        <p className="text-gray-500 dark:text-gray-400 text-center max-w-md">
          Where do you want to go today? I can help you plan the perfect trip.
        </p>
      </div>

      {/* Suggestion Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
        {suggestions.map((item, index) => (
          <div 
            key={index}
            onClick={() => setPrompt(item.text)}
            className="
              flex items-center gap-4 p-4 rounded-xl cursor-pointer transition-all duration-300
              bg-gray-50 border border-gray-100 
              hover:bg-blue-50 hover:border-blue-200 hover:shadow-md hover:-translate-y-1
              dark:bg-[#2d2d2d] dark:border-gray-700 dark:hover:bg-[#3d3d3d] dark:hover:border-gray-600
            "
          >
            <div className="p-2bg-white dark:bg-gray-800 rounded-lg text-blue-500 dark:text-blue-400 shadow-sm">
              {item.icon}
            </div>
            <div className="flex flex-col items-start overflow-hidden">
               <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-0.5">{item.label}</span>
               <span className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate w-full text-left">{item.text}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const ChatBox = ({ onShowMap }) => {
  const {selectedChat, theme, axios, user, token, schedulePlaces, setSchedulePlaces, showPreviewLocation, setShowPreviewLocation} = useAppContext();
  const [message, setMessage] = useState([]);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);
  const [prompt, setPrompt] = useState('');
  const [placeDetails, setPlaceDetails] = useState({});
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [showPlaceModal, setShowPlaceModal] = useState(false);

  // Auto scroll
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [message, loading]);

  const handleDisplayMap = (msg) => {
    try {
        if (msg.originJson) {
            onShowMap(msg.originJson);
            return;
        }
    } catch (error) {
        toast.error("Không thể đọc dữ liệu lịch trình");
    }
  };

  // Handle suggestion click - send as new message
  const handleSuggestionClick = (suggestionText) => {
    setPrompt(suggestionText);
    // Auto-submit after a short delay
    setTimeout(() => {
      const form = document.querySelector('form');
      if (form) {
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      }
    }, 100);
  };

  // Handle adding place to itinerary
  const handleAddToItinerary = async () => {
    try {
      if (!selectedPlace || !selectedChat) {
        toast.error('Cannot add to itinerary');
        return;
      }

      toast.loading('Adding to itinerary...');

      // Get current schedule places (or empty array if none)
      const currentPlaces = schedulePlaces || [];
      
      // Add selected place to the end
      const newPlaces = [...currentPlaces, selectedPlace];
      
      // Update context to sync with Schedule and RoutineMap
      setSchedulePlaces(newPlaces);
      
      // Update database
      const sortedRowIds = newPlaces.map((item) => item.rowid).filter(Boolean);
      if (sortedRowIds.length) {
        await axios.post('/api/message/newSequence', {
          chatID: selectedChat._id,
          sequence: sortedRowIds
        }, { headers: { Authorization: token } });
      }

      toast.dismiss();
      toast.success(`${selectedPlace.Name} added to itinerary!`);
      
      // Close modal
      setShowPlaceModal(false);
      setSelectedPlace(null);
    } catch (error) {
      console.error('Error adding to itinerary:', error);
      toast.dismiss();
      toast.error('Failed to add to itinerary');
    }
  };

  // Handle showing place details
  const handleShowPlaceDetails = async (placeId, place) => {
    try {
      // If we already have detailed info, show it
      if (place && place.Categories) {
        setSelectedPlace(place);
        setShowPlaceModal(true);
        return;
      }

      // Otherwise fetch from backend
      toast.loading('Loading place details...');
      const response = await axios.post(
        '/api/static_db/query',
        { list_id: [placeId] },
        { headers: { Authorization: token } }
      );

      toast.dismiss();

      if (response.data && response.data.data && response.data.data.length > 0) {
        const item = response.data.data[0];
        
        // Parse data like in the example
        const safeParseList = (str) => {
          if (!str) return [];
          try {
            const parsed = JSON.parse(str);
            return Array.isArray(parsed) ? parsed : [];
          } catch (e) {
            return [];
          }
        };

        let parsedCategories = safeParseList(item.categories);
        if (parsedCategories.length === 0) parsedCategories = ["Place"];

        let parsedImages = safeParseList(item.images);
        
        let parsedReviews = [];
        try { if (item.reviews) parsedReviews = JSON.parse(item.reviews); } catch (e) {}
        
        let hoursObj = {};
        try { if (item.openingHours) hoursObj = JSON.parse(item.openingHours); } catch (e) {}

        const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
        const displayHours = hoursObj[today] || "Not available";

        const detailedPlace = {
          rowid: item.rowid,
          id: item.id || placeId,
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
          Lon: item.location_lon || item.lon
        };

        setSelectedPlace(detailedPlace);
        setShowPlaceModal(true);
        
        // Update placeDetails cache with consistent structure
        setPlaceDetails(prev => ({
          ...prev,
          [placeId]: {
            ...detailedPlace,
            // Ensure both formats are available for compatibility
            name: detailedPlace.Name,
            address: detailedPlace.Address,
            rating: detailedPlace.Rating,
            images: detailedPlace.Image_URLs,
            lat: detailedPlace.Lat,
            lon: detailedPlace.Lon
          }
        }));
      } else {
        toast.error('Place details not found');
      }
    } catch (error) {
      console.error(error);
      toast.dismiss();
      toast.error('Failed to load place details');
    }
  };

  // Handle preview location on map
  const handlePreviewOnMap = (placeId, place) => {
    console.log('Previewing place on map:', placeId, place);
    if (!place || (!place.Lat && !place.lat) || (!place.Lon && !place.lon)) {
      toast.error('Location coordinates not available');
      return;
    }

    const previewLocation = {
      lat: parseFloat(place.Lat || place.lat),
      lon: parseFloat(place.Lon || place.lon),
      name: place.Name || place.name || 'Suggested Location',
      address: place.Address || place.address,
      rating: place.Rating || place.rating
    };

    setShowPreviewLocation([previewLocation]);
    toast.success('Location previewed on map!');
  };

  // Handle adding place to schedule directly from suggested locations
  const handleAddToSchedule = async (placeId, place) => {
    try {
      if (!selectedChat) {
        toast.error('No chat selected');
        return;
      }

      // If place doesn't have complete info, fetch it
      let placeToAdd = place;
      if (!place || !place.Name) {
        toast.loading('Loading place details...');
        const response = await axios.post(
          '/api/static_db/query',
          { list_id: [placeId] },
          { headers: { Authorization: token } }
        );
        toast.dismiss();

        if (response.data && response.data.data && response.data.data.length > 0) {
          const item = response.data.data[0];
          
          const safeParseList = (str) => {
            if (!str) return [];
            try {
              const parsed = JSON.parse(str);
              return Array.isArray(parsed) ? parsed : [];
            } catch (e) {
              return [];
            }
          };

          let parsedCategories = safeParseList(item.categories);
          if (parsedCategories.length === 0) parsedCategories = ["Place"];

          let parsedImages = safeParseList(item.images);

          placeToAdd = {
            rowid: item.rowid,
            id: item.id || placeId,
            Name: item.name || item.title || item.address?.split(',')[0] || "Unknown",
            Address: item.address || "",
            Categories: parsedCategories,
            Image_URLs: parsedImages,
            Rating: item.rating || 0,
            Lat: item.location_lat || item.lat,
            Lon: item.location_lon || item.lon
          };
        } else {
          toast.error('Place not found');
          return;
        }
      }

      toast.loading('Adding to schedule...');

      // Get current schedule places (or empty array if none)
      const currentPlaces = schedulePlaces || [];
      
      // Check if place already exists in schedule
      const alreadyExists = currentPlaces.some(p => p.rowid === placeToAdd.rowid || p.id === placeToAdd.id);
      if (alreadyExists) {
        toast.dismiss();
        toast.error('This place is already in your schedule');
        return;
      }
      
      // Add selected place to the end
      const newPlaces = [...currentPlaces, placeToAdd];
      
      // Update context to sync with Schedule and RoutineMap
      setSchedulePlaces(newPlaces);
      
      // Update database
      const sortedRowIds = newPlaces.map((item) => item.rowid).filter(Boolean);
      if (sortedRowIds.length) {
        await axios.post('/api/message/newSequence', {
          chatID: selectedChat._id,
          sequence: sortedRowIds
        }, { headers: { Authorization: token } });
      }

      toast.dismiss();
      toast.success(`${placeToAdd.Name} added to schedule!`);
    } catch (error) {
      console.error('Error adding to schedule:', error);
      toast.dismiss();
      toast.error('Failed to add to schedule');
    }
  };

  // Fetch place details when database_results are present
  useEffect(() => {
    const fetchPlaceDetails = async () => {
      const allPlaceIds = new Set();
      
      // Collect all place IDs from messages
      message.forEach(msg => {
        if (msg.database_results && msg.database_results.length > 0) {
          msg.database_results.forEach(id => allPlaceIds.add(id));
        }
      });

      if (allPlaceIds.size === 0) return;

      try {
        // Fetch details for places we don't have yet
        const idsToFetch = Array.from(allPlaceIds).filter(id => !placeDetails[id]);
        
        if (idsToFetch.length > 0) {
          const response = await axios.post(
            '/api/static_db/query',
            { list_id: idsToFetch },
            { headers: { Authorization: token } }
          );

          if (response.data && response.data.data) {
            const safeParseList = (str) => {
              if (!str) return [];
              try {
                const parsed = JSON.parse(str);
                return Array.isArray(parsed) ? parsed : [];
              } catch (e) {
                return [];
              }
            };

            const placesMap = {};
            response.data.data.forEach(item => {
              let parsedImages = safeParseList(item.images);
              placesMap[item.rowid] = {
                name: item.name || item.title,
                address: item.address,
                rating: item.rating,
                Image_URLs: parsedImages,
                Lat: item.location_lat || item.lat,
                Lon: item.location_lon || item.lon
              };
            });
            setPlaceDetails(prev => ({
              ...prev,
              ...placesMap
            }));
          }
        }
      } catch (error) {
        console.error('Failed to fetch place details:', error);
      }
    };

    fetchPlaceDetails();
  }, [message, axios, token, placeDetails]);

  const onsubmit = async (e) => {
    try {
      e.preventDefault();
      if (!prompt.trim()) return; 
      if (!user) return;
      
      setLoading(true);
      const promptcopy = prompt;
      setPrompt('');
      
      const newUserMsg = { role: 'user', content: promptcopy, timestamp: new Date() };
      setMessage(prev => [...prev, newUserMsg]);
      
      const {data} = await axios.post('/api/message/text', { chatID : selectedChat._id, prompt: promptcopy }, { headers: { Authorization: token} });
      
      if (data.success) {
        let replyMsg = data.reply;
        try {
            if(replyMsg.content.startsWith('{')) {
                const json = JSON.parse(replyMsg.content);
                if(json.path) {
                    replyMsg.originJson = json;
                }
            }
        } catch(e) {}

        setMessage(prev => [...prev, replyMsg]);
        
        if (selectedChat && selectedChat.messages) {
            selectedChat.messages.push(newUserMsg); 
            selectedChat.messages.push(replyMsg); 
        }
      } else {
        toast.error(data.message || "Failed");
      }
    } catch (error) {
      console.error(error);
      toast.error("Failed to send");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (selectedChat) {
        const processedMsgs = selectedChat.messages.map(m => {
            try {
                if (m.role === 'assistant' && typeof m.content === 'string' && m.content.startsWith('{"path"')) {
                    return { ...m, originJson: JSON.parse(m.content) };
                }
            } catch (e) {}
            return m;
        });
        setMessage(processedMsgs);
    }
  }, [selectedChat]);

  return (
    <div className='h-full flex flex-col justify-between p-4 pt-14 bg-white dark:bg-[#1a1a1a]'>
      
      {/* Container tin nhắn */}
      <div ref={containerRef} className='flex-1 mb-5 overflow-y-scroll no-scrollbar scroll-smooth'>
         
         {message.length === 0 ? (
            <EmptyState setPrompt={setPrompt} />
         ) : (
            <div className="flex flex-col gap-4 animate-fadeIn">
                {message.map((msg, index) => (
                    <Message 
                        key={index} 
                        message={msg} 
                        onDisplay={() => handleDisplayMap(msg)}
                        onSuggestionClick={handleSuggestionClick}
                        onShowPlaceDetails={handleShowPlaceDetails}
                        onPreviewOnMap={handlePreviewOnMap}
                        onAddToSchedule={handleAddToSchedule}
                        placeDetails={placeDetails}
                    />
                ))}

                {loading && (
                  <div className="flex items-start gap-2.5">
                    <img src={assets.gemini_icon} className="w-8 h-8 rounded-full p-1 border border-gray-200 dark:border-gray-700 bg-white dark:bg-black" alt="AI" />
                    
                    <div className="flex flex-col w-full max-w-[100px] leading-1.5 p-4 border-gray-200 bg-gray-100 rounded-e-xl rounded-es-xl dark:bg-[#2d2d2d]">
                        <div className="flex space-x-2 justify-center items-center">
                            <div className='h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]'></div>
                            <div className='h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]'></div>
                            <div className='h-2 w-2 bg-gray-400 rounded-full animate-bounce'></div>
                        </div>
                    </div>
                  </div>
                )}
            </div>
         )}

      </div>
      
      {/* Input Form */}
      {/* CẬP NHẬT 2: Xóa class 'z-20' để không bị đè lên Sidebar */}
      <form onSubmit={onsubmit} className='flex items-center gap-2 p-2 px-4 bg-gray-100 dark:bg-[#2d2d2d] rounded-3xl shadow-sm border border-transparent focus-within:border-gray-300 dark:focus-within:border-gray-600 transition-all'>
         <input 
            onChange={(e)=>setPrompt(e.target.value)} 
            value={prompt} 
            type='text' 
            placeholder='Ask me about your next trip...' 
            className='flex-1 bg-transparent outline-none dark:text-white placeholder-gray-400' 
         />
         <button disabled={loading || !prompt.trim()} className={`p-2 rounded-full text-white transition-all ${loading || !prompt.trim() ? 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 shadow-lg hover:shadow-blue-500/30'}`}>
             <img src={assets.send_icon} className='w-4 h-4 invert' alt="send" />
         </button>
      </form>

      {/* Place Details Modal */}
      {showPlaceModal && selectedPlace && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onClick={() => setShowPlaceModal(false)}>
          <div className="bg-white dark:bg-[#1a1a1a] rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="sticky top-0 bg-white dark:bg-[#1a1a1a] border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between z-10">
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Place Details</h2>
              <button onClick={() => setShowPlaceModal(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 text-gray-600 dark:text-gray-400">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              {/* Images */}
              {selectedPlace.Image_URLs && selectedPlace.Image_URLs.length > 0 && (
                <div className="mb-6">
                  <img src={selectedPlace.Image_URLs[0]} alt={selectedPlace.Name} className="w-full h-64 object-cover rounded-xl" onError={(e) => e.target.style.display = 'none'} />
                  {selectedPlace.Image_URLs.length > 1 && (
                    <div className="grid grid-cols-4 gap-2 mt-2">
                      {selectedPlace.Image_URLs.slice(1, 5).map((img, idx) => (
                        <img key={idx} src={img} alt="" className="w-full h-20 object-cover rounded-lg" onError={(e) => e.target.style.display = 'none'} />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Name & Rating */}
              <div className="mb-4">
                <h3 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">{selectedPlace.Name}</h3>
                {selectedPlace.Rating > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="flex items-center">
                      {[...Array(5)].map((_, i) => (
                        <svg key={i} className={`w-5 h-5 ${i < Math.floor(selectedPlace.Rating) ? 'text-yellow-500' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                    <span className="text-gray-600 dark:text-gray-400 font-medium">{selectedPlace.Rating.toFixed(1)}</span>
                  </div>
                )}
              </div>

              {/* Categories */}
              {selectedPlace.Categories && selectedPlace.Categories.length > 0 && (
                <div className="mb-4 flex flex-wrap gap-2">
                  {selectedPlace.Categories.map((cat, idx) => (
                    <span key={idx} className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 rounded-full text-sm font-medium">
                      {cat}
                    </span>
                  ))}
                </div>
              )}

              {/* Address */}
              {selectedPlace.Address && (
                <div className="mb-4 flex items-start gap-3">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-gray-500 mt-0.5 flex-shrink-0">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                  </svg>
                  <p className="text-gray-600 dark:text-gray-400">{selectedPlace.Address}</p>
                </div>
              )}

              {/* Opening Hours */}
              {selectedPlace.Opening_Hours && (
                <div className="mb-4 flex items-start gap-3">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-gray-500 mt-0.5 flex-shrink-0">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-gray-600 dark:text-gray-400">{selectedPlace.Opening_Hours}</p>
                </div>
              )}

              {/* Phone */}
              {selectedPlace.Phone && (
                <div className="mb-4 flex items-start gap-3">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-gray-500 mt-0.5 flex-shrink-0">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
                  </svg>
                  <a href={`tel:${selectedPlace.Phone}`} className="text-blue-600 dark:text-blue-400 hover:underline">{selectedPlace.Phone}</a>
                </div>
              )}

              {/* Website */}
              {selectedPlace.Website && (
                <div className="mb-4 flex items-start gap-3">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-gray-500 mt-0.5 flex-shrink-0">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                  </svg>
                  <a href={selectedPlace.Website} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline break-all">{selectedPlace.Website}</a>
                </div>
              )}

              {/* Description */}
              {selectedPlace.Description && (
                <div className="mb-4">
                  <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">Description</h4>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{selectedPlace.Description}</p>
                </div>
              )}

              {/* Reviews */}
              {selectedPlace.Reviews && selectedPlace.Reviews.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3">Reviews</h4>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {selectedPlace.Reviews.slice(0, 5).map((review, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-gray-700 dark:text-gray-200">{review.author || 'Anonymous'}</span>
                          {review.rating && (
                            <div className="flex items-center">
                              {[...Array(5)].map((_, i) => (
                                <svg key={i} className={`w-3 h-3 ${i < review.rating ? 'text-yellow-500' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                              ))}
                            </div>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{review.text || review.comment}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Button - Add to Itinerary */}
              <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button 
                  onClick={handleAddToItinerary}
                  className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                  </svg>
                  Add to Itinerary
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatBox