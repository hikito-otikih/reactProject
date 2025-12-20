import React, { useState, useRef, useEffect } from 'react';
import { MapPin, Clock, GripVertical, Trash2, Plus, Image as ImageIcon, X, Loader2, Star, Globe, Phone, ChevronLeft, ChevronRight, MessageSquareQuote, Search as SearchIcon } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import toast from 'react-hot-toast';

// --- SUB-COMPONENT: REVIEW SLIDER ---
const ReviewSlider = ({ reviews, theme }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const validReviews = reviews ? reviews.filter(r => r.text && r.text.trim() !== "") : [];

  if (!validReviews || validReviews.length === 0) return null;

  const nextReview = (e) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev + 1) % validReviews.length);
  };

  const prevReview = (e) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev - 1 + validReviews.length) % validReviews.length);
  };

  const currentReview = validReviews[currentIndex];

  return (
    <div className={`rounded-xl p-3 mt-3 relative group/review transition-colors duration-300 ${theme === 'dark' ? 'bg-slate-700/80 border border-blue-500/60' : 'bg-blue-50 border border-blue-100'}`}>
      
      {validReviews.length > 1 && (
        <button 
          onClick={prevReview}
          className={`absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 p-1 rounded-full shadow-md z-10 opacity-0 group-hover/review:opacity-100 transition-all ${theme === 'dark' ? 'bg-slate-600 text-white hover:bg-slate-500' : 'bg-white text-gray-600 hover:bg-gray-100'}`}
        >
          <ChevronLeft size={16} />
        </button>
      )}

      {validReviews.length > 1 && (
        <button 
          onClick={nextReview}
          className={`absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 p-1 rounded-full shadow-md z-10 opacity-0 group-hover/review:opacity-100 transition-all ${theme === 'dark' ? 'bg-slate-600 text-white hover:bg-slate-500' : 'bg-white text-gray-600 hover:bg-gray-100'}`}
        >
          <ChevronRight size={16} />
        </button>
      )}

      <div className="flex gap-3">
        <MessageSquareQuote size={20} className="shrink-0 text-blue-400 mt-1" />
        <div className="flex-1">
          <div className="flex justify-between items-start mb-1">
            <span className={`font-bold text-xs ${theme === 'dark' ? 'text-gray-200' : 'text-gray-800'}`}>
              {currentReview.name}
            </span>
            <div className="flex items-center gap-0.5">
              <span className={`text-[10px] font-bold ${theme === 'dark' ? 'text-yellow-400' : 'text-yellow-600'}`}>{currentReview.stars}</span>
              <Star size={8} fill="currentColor" className={theme === 'dark' ? 'text-yellow-400' : 'text-yellow-500'} />
            </div>
          </div>
          <p className={`text-[11px] leading-relaxed line-clamp-3 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            "{currentReview.text}"
          </p>
        </div>
      </div>

      {validReviews.length > 1 && (
        <div className="flex justify-center gap-1.5 mt-2">
          {validReviews.map((_, idx) => (
            <div 
              key={idx}
              className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${idx === currentIndex ? (theme === 'dark' ? 'bg-blue-400 w-3' : 'bg-blue-500 w-3') : (theme === 'dark' ? 'bg-slate-600' : 'bg-gray-300')}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Lightweight image component: retries via proxy once, then falls back to a placeholder
const buildProxyUrl = (url) => `https://images.weserv.nl/?url=${encodeURIComponent(url)}`;

const ScheduleImage = ({ src, theme, onClick, onFinalError }) => {
  const [currentSrc, setCurrentSrc] = useState(src);
  const [failed, setFailed] = useState(false);
  const [triedProxy, setTriedProxy] = useState(false);

  const handleError = () => {
    if (!triedProxy) {
      setTriedProxy(true);
      setCurrentSrc(buildProxyUrl(src));
      return;
    }
    setFailed(true);
    if (onFinalError) onFinalError(src);
  };

  if (failed) {
    return (
      <div
        className={`h-20 w-20 rounded-lg flex flex-col items-center justify-center gap-1 shadow-sm snap-start shrink-0 cursor-pointer hover:opacity-80 transition-opacity ${theme === 'dark' ? 'bg-gray-900 border border-gray-700' : 'bg-gray-50 border border-gray-200'}`}
        onClick={() => window.open(src, '_blank')}
        title="Click để mở ảnh"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className={`w-5 h-5 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span className={`text-[8px] text-center ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>Load error</span>
      </div>
    );
  }

  return (
    <img
      src={currentSrc}
      alt="img"
      loading="lazy"
      referrerPolicy="no-referrer"
      className={`h-20 w-auto min-w-[100px] rounded-lg object-cover shadow-sm hover:scale-[1.02] transition-transform cursor-zoom-in snap-start shrink-0 ${theme === 'dark' ? 'bg-gray-900 border border-gray-700' : 'bg-gray-50 border border-gray-200'}`}
      onClick={onClick}
      onError={handleError}
      onLoad={() => console.log('Ảnh tải thành công:', currentSrc)}
    />
  );
};

// Avatar image with proxy retry and graceful fallback
const AvatarImage = ({ src, theme }) => {
  const placeholder = "https://via.placeholder.com/80?text=Place";
  const [currentSrc, setCurrentSrc] = useState(src || placeholder);
  const [failed, setFailed] = useState(false);
  const [triedProxy, setTriedProxy] = useState(false);

  const handleError = () => {
    if (!triedProxy && src) {
      setTriedProxy(true);
      setCurrentSrc(buildProxyUrl(src));
      return;
    }
    setFailed(true);
  };

  if (failed) {
    return (
      <div className={`w-full h-full flex items-center justify-center text-[10px] font-semibold ${theme === 'dark' ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-500'}`}>
        N/A
      </div>
    );
  }

  return (
    <img
      src={currentSrc}
      alt="avatar"
      referrerPolicy="no-referrer"
      className="w-full h-full object-cover"
      onError={handleError}
    />
  );
};

// --- MAIN COMPONENT ---
const Schedule = () => {
  const { selectedImage, setSelectedImage, theme, axios, selectedChat, token, schedulePlaces, setSchedulePlaces, showPreviewLocation, setShowPreviewLocation } = useAppContext();
  
  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [newItemId, setNewItemId] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [insertIndex, setInsertIndex] = useState(null);
  const [categoryOptions, setCategoryOptions] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [resultIds, setResultIds] = useState([]);
  const [resultPlaces, setResultPlaces] = useState([]);
  const [resultLoading, setResultLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchName, setSearchName] = useState('');
  const [positionIdx, setPositionIdx] = useState('');
  const [kCount, setKCount] = useState('');
  const [suggestLoading, setSuggestLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('name');
  const [showBulkAdd, setShowBulkAdd] = useState(false);
  
  const dragItem = useRef(null);
  const dragOverItem = useRef(null);
  const itemRefs = useRef({});
  const resultScrollRef = useRef(null);
  const schedulePlacesRef = useRef([]);

// --- FETCH DATA ---
  // ... (giữ nguyên useEffect fetch data cũ) ...

  // --- ĐỒNG BỘ DỮ LIỆU TỪ CONTEXT (SỬA ĐOẠN NÀY) ---
  useEffect(() => {
    // 1. Cập nhật Ref (để logic cũ vẫn chạy đúng)
    schedulePlacesRef.current = schedulePlaces;

    // 2. Cập nhật State hiển thị (quan trọng để UI tự vẽ lại ngay lập tức)
    // Kiểm tra nếu schedulePlaces có dữ liệu thì mới set để tránh lỗi lúc khởi tạo
    if (schedulePlaces && Array.isArray(schedulePlaces)) {
        setPlaces(schedulePlaces);
    }
  }, [schedulePlaces]);

  // --- SAFE PARSE HELPER ---
  const safeParseList = (str) => {
    if (!str) return [];
    try {
      return JSON.parse(str);
    } catch (e) {
      return str.replace(/[\[\]]/g, '').split(',').map(s => s.trim()).filter(s => s !== "");
    }
  };

  // --- FETCH DATA ---
  useEffect(() => {
    const fetchScheduleData = async () => {
      if (!selectedChat || !selectedChat.sequence || selectedChat.sequence.length === 0) {
        setPlaces([]);
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        //console.log("Fetching schedule data for sequence:", selectedChat.sequence);
        const response = await axios.post('/api/static_db/query', {
          list_id: selectedChat.sequence
        });

        if (response.data.success) {
          //console.log("Raw schedule data:", response.data.data);
          const formattedData = response.data.data.map((item, index) => {
            
            // Xử lý dữ liệu an toàn
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
              Lat: item.location_lat,
              Lon: item.location_lon
            };
          });
          setPlaces(formattedData);
          setSchedulePlaces(formattedData); // Sync with context
          console.log('Loaded schedule places:', formattedData);
        }
      } catch (error) {
        console.error("Fetch error:", error);
        toast.error("Không thể tải dữ liệu");
      } finally {
        setLoading(false);
      }
    };
    fetchScheduleData();
  }, [selectedChat]);

  // Load details for resultIds to render preview cards
  useEffect(() => {
    if (!resultIds.length) {
      setResultPlaces([]);
      return;
    }
    let cancelled = false;
    const load = async () => {
      setResultLoading(true);
      const data = await fetchPlacesByIds(resultIds);
      if (!cancelled) setResultPlaces(data);
      setResultLoading(false);
    };
    load();
    return () => { cancelled = true; };
  }, [resultIds]);

  // Helper Functions
  const getValidImages = (urls) => (Array.isArray(urls) ? urls.filter(u => u && u.startsWith('http')) : []);
  const getAvatarImage = (urls) => {
    const valid = getValidImages(urls);
    return valid.length > 0 ? valid[0] : "https://via.placeholder.com/100?text=Place";
  };

  const handleSort = () => {
    let _places = [...places];
    const draggedItemContent = _places.splice(dragItem.current, 1)[0];
    _places.splice(dragOverItem.current, 0, draggedItemContent);
    dragItem.current = null;
    dragOverItem.current = null;
    setPlaces(_places);
    setSchedulePlaces(_places); // Sync with context
    const sortedRowIds = _places.map((item) => item.rowid);
    axios.post('/api/message/newSequence', {
      chatID: selectedChat._id,
      sequence: sortedRowIds
    }, { headers: { Authorization: token} });
  };

  // --- ADD PLACE WIZARD ---
  const openAddWizard = (index) => {
    setInsertIndex(index);
    setShowAddModal(true);
    loadDemoCategories();
    setSelectedIds([]);
    setResultIds([]);
  };

  const closeAddWizard = () => {
    setShowAddModal(false);
    setInsertIndex(null);
    setSelectedIds([]);
    setResultIds([]);
    setSelectedCategories([]);
  };

  const loadDemoCategories = async () => {
    console.log('Loading categories for chat:', selectedChat?._id);
    try {
      const response = await axios.get('/api/message/getSuggestCategory', {
        params: { chatID: selectedChat._id },
        headers: { Authorization: token }
      });
      console.log('Category response:', response.data.categories.data);
      
      // Parse categories from API response: {data: ['leisure'], success: true}
      let categories = [];
      if (Array.isArray(response.data.categories.data)) {
        categories = response.data.categories.data;
      } else {
        // convert to array if it's a single element
        categories = [response.data.categories.data];
      }
      
      console.log('Parsed categories array:', categories);
      setCategoryOptions(categories);
    } catch (error) {
      console.error("Error loading categories:", error.response?.data || error.message);
      toast.error('Không thể tải danh mục gợi ý');
      setCategoryOptions([]);
    }
  };

  const toggleCategory = (cat) => {
    setSelectedCategories((prev) => prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]);
  };

  const fetchPlacesByIds = async (ids) => {
    try {
      const response = await axios.post('/api/static_db/query', { list_id: ids });
      if (response.data?.success && Array.isArray(response.data.data)) {
        return response.data.data.map((item, index) => {
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
            Lat: item.location_lat,
            Lon: item.location_lon
          };
        });
      }
      return [];
    } catch (error) {
      toast.error('Không thể tải danh sách địa điểm');
      return [];
    }
  };

  const demoSetResultIds = (ids) => {
    setResultIds(ids);
    setSelectedIds(ids.slice(0, 3));
  };

  const handleSearchByName = async () => {
    try {
      setSuggestLoading(true);
      const response = await axios.get('/api/message/getSearchByName', {
        params: { name: searchName, exact: true, limit: 10 },
        headers: { Authorization: token }
      });
      console.log('Search response:', response.data);
      
      // Safely access nested data
      const demoIds = response.data?.results?.data || response.data?.data || [];
      
      if (!demoIds.length) {
        toast.error('No results found');
        setSuggestLoading(false);
        return;
      }
      
      demoSetResultIds(demoIds);
      //console.log("Setting result IDs from search:", resultIds);
      setSuggestLoading(false);
    } catch (error) {
      console.error("Error searching:", error.response?.data || error.message);
      toast.error("Cannot search by name");
      setSuggestLoading(false);
    }
  };

  const handleSuggestByPosition = async () => {
    try {
      setSuggestLoading(true);
      // Demo backend result, replace with real call
      const response = await axios.get('/api/message/getSuggestForPosition', {
        params: { chatID: selectedChat?._id, category: selectedCategories?.[0], position: insertIndex, limit: 10 },
        headers: { Authorization: token }
      });
      console.log(`category selected: ${selectedCategories?.[0]}, position: ${insertIndex}`);
      console.log('Suggest by position response:', response.data);
      
      // Safely access nested data
      const demoIds = response.data?.suggestions?.data || response.data?.data || [];
      
      if (!demoIds.length) {
        toast.error('No suggestions found');
        setSuggestLoading(false);
        return;
      }
      
      demoSetResultIds(demoIds);
      setSuggestLoading(false);
    } catch (error) {
      console.error("Error suggesting by position:", error.response?.data || error.message);
      toast.error("Cannot suggest by position");
      setSuggestLoading(false);
    }
  };

  const handleAddKPlaces = async () => {
    const k = parseInt(kCount);
    if (!k || k < 1 || k > 20) {
      toast.error('Please enter a valid number between 1 and 20');
      return;
    }
    try {
      setSuggestLoading(true);
      const response = await axios.get('/api/message/addKPlaces', {
        params: { chatID: selectedChat?._id, limit: k },
        headers: { Authorization: token }
      });
      console.log(`Adding ${k} places to the end of schedule`);
      console.log('Add K places response:', response.data);
      
      // Safely access nested data
      const demoIds = response.data?.suggestions?.data || response.data?.data || [];
      
      if (!demoIds.length) {
        toast.error('No places found');
        setSuggestLoading(false);
        return;
      }
      
      // Fetch full place details
      const data = await fetchPlacesByIds(demoIds);
      if (!data.length) {
        toast.error('No places found');
        setSuggestLoading(false);
        return;
      }
      
      // Append to end of places array
      const newPlaces = [...places, ...data];
      setPlaces(newPlaces);
      setSchedulePlaces(newPlaces); // Sync with context
      setNewItemId(data[0]?.id);
      setTimeout(() => { if (data[0]) setExpandedId(data[0].id); }, 300);
      setTimeout(() => { setNewItemId(null); }, 1200);
      
      // Close popup and reset
      setShowBulkAdd(false);
      setKCount('');
      
      // Update backend sequence
      const sortedRowIds = newPlaces.map((item) => item.rowid).filter(Boolean);
      if (sortedRowIds.length) {
        await axios.post('/api/message/newSequence', {
          chatID: selectedChat?._id,
          sequence: sortedRowIds
        }, { headers: { Authorization: token} });
      }
      
      toast.success(`Added ${data.length} places to your schedule`);
      setSuggestLoading(false);
    } catch (error) {
      console.error("Error adding k places:", error.response?.data || error.message);
      toast.error("Cannot add places");
      setSuggestLoading(false);
    }
  };

  const handleApplySelected = async () => {
    if (!selectedIds.length) {
      toast.error('Chọn ít nhất 1 địa điểm');
      return;
    }
    const data = await fetchPlacesByIds(selectedIds);
    if (!data.length) return;
    const newPlaces = [...places];
    const insertAt = insertIndex ?? newPlaces.length;
    newPlaces.splice(insertAt, 0, ...data);
    //console.log('New places after addition:', newPlaces);
    setPlaces(newPlaces);
    setSchedulePlaces(newPlaces); // Sync with context
    setNewItemId(data[0]?.id);
    setTimeout(() => { if (data[0]) setExpandedId(data[0].id); }, 300);
    setTimeout(() => { setNewItemId(null); }, 1200);
    closeAddWizard();
    const sortedRowIds = newPlaces.map((item) => item.rowid).filter(Boolean);
    if (sortedRowIds.length) {
      axios.post('/api/message/newSequence', {
        chatID: selectedChat?._id,
        sequence: sortedRowIds
      }, { headers: { Authorization: token} });
    }
  };

  const handlePreviewPlace = (place, e) => {
    e.stopPropagation();
    if (!place.Lat || !place.Lon) {
      toast.error('Không có tọa độ để xem trước');
      return;
    }
    const previewLocation = {
      lat: place.Lat,
      lon: place.Lon,
      name: place.Name,
      address: place.Address,
      rating: place.Rating
    };
    setShowPreviewLocation([previewLocation]);
    toast.success('Đã hiển thị địa điểm trên bản đồ');
  };

  const handleDelete = (id, e) => {
    e.stopPropagation();
    const newPlaces = places.filter(item => item.id !== id);
    setPlaces(newPlaces);
    setSchedulePlaces(newPlaces); // Sync with context
    const sortedRowIds = newPlaces.map((item) => item.rowid);
    axios.post('/api/message/newSequence', {
      chatID: selectedChat._id,
      sequence: sortedRowIds
    }, { headers: { Authorization: token} });
  };

  const openLightbox = (imgUrl, e) => {
    e.stopPropagation();
    setSelectedImage(imgUrl);
  };

  const handleImageError = (imgUrl) => {
    console.error('Lỗi tải ảnh trong Schedule:', imgUrl);
  };

  const scrollResultList = (direction) => {
    if (resultScrollRef.current) {
      const scrollAmount = 280; // width of card + gap
      const currentScroll = resultScrollRef.current.scrollLeft;
      resultScrollRef.current.scrollTo({
        left: direction === 'left' ? currentScroll - scrollAmount : currentScroll + scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    if (expandedId && itemRefs.current[expandedId]) {
      setTimeout(() => {
        itemRefs.current[expandedId].scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
      }, 500); 
    }
  }, [expandedId]);

  useEffect(() => {
    if (newItemId && itemRefs.current[newItemId]) {
      itemRefs.current[newItemId].scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [newItemId]);

  const InsertButton = ({ index }) => (
    <div 
      className="group/insert relative h-4 flex items-center justify-center cursor-pointer transition-all duration-200 z-10"
      onClick={() => openAddWizard(index)}
    >
      <div className={`px-3 py-1.5 rounded-full flex items-center gap-1.5 transition-all duration-300 transform opacity-0 group-hover/insert:opacity-100 translate-y-2 group-hover/insert:translate-y-0 shadow-lg hover:shadow-xl hover:scale-105 ${theme === 'dark' ? 'bg-blue-600 text-white border border-blue-500' : 'bg-blue-500 text-white border border-blue-400'}`}>
        <Plus size={12} strokeWidth={3}/>
        <span className="text-[11px] font-bold">Add Destination</span>
      </div>
    </div>
  );

  return (
    <>
      <style>{`
        @keyframes dramaticEnter {
          0% { opacity: 0; transform: translateX(100%) scale(0.5); max-height: 0px; margin: 0; }
          50% { opacity: 0.5; max-height: 100px; margin: 1rem 0; }
          80% { transform: translateX(-10px) scale(1.05); }
          100% { opacity: 1; transform: translateX(0) scale(1); max-height: 500px; }
        }
        @keyframes slideInLeft {
          0% { opacity: 0; transform: translateX(-100%); }
          100% { opacity: 1; transform: translateX(0); }
        }
        .custom-scrollbar::-webkit-scrollbar { height: 6px !important; width: 6px; display: block !important; }
        .custom-scrollbar::-webkit-scrollbar-track { background: ${theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'}; border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background-color: ${theme === 'dark' ? '#4b5563' : '#cbd5e1'}; border-radius: 4px; }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>

      <div className={`h-full flex flex-col pt-10 relative overflow-y-auto overflow-x-hidden px-4 bg-transparent`}>
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-2">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <span className="text-xs">Đang tải dữ liệu...</span>
          </div>
        ) : (
          <div className="relative flex flex-col w-full min-h-full z-10 pb-32">
              {places.map((place, index) => {
                  const isExpanded = expandedId === place.id;
                  const validImages = getValidImages(place.Image_URLs);
                  const isNew = place.id === newItemId;

                  return (
                  <React.Fragment key={place.id}>
                      <InsertButton index={index} />

                      <div
                          ref={(el) => (itemRefs.current[place.id] = el)}
                          className={`
                              relative z-10 group/item rounded-2xl p-4
                              ${isNew ? 'animate-[dramaticEnter_0.7s_cubic-bezier(0.34,1.56,0.64,1)_forwards]' : ''}
                              transition-all duration-500 cubic-bezier(0.2, 0.8, 0.2, 1)
                              ${isExpanded 
                                  ? `my-8 scale-100 shadow-2xl z-20 cursor-default ${theme === 'dark' ? 'bg-slate-800 border-blue-500' : 'bg-white border-blue-500'}` 
                                  : `my-2 scale-100 shadow-lg hover:scale-[1.01] hover:shadow-xl cursor-pointer flex flex-row-reverse items-start gap-4 ${theme === 'dark' ? 'bg-slate-800/80 border-gray-700' : 'bg-white border-gray-200'}`
                              }
                              border
                          `}
                          draggable={!isExpanded}
                          onDragStart={(e) => (dragItem.current = index)}
                          onDragEnter={(e) => (dragOverItem.current = index)}
                          onDragEnd={handleSort}
                          onDragOver={(e) => e.preventDefault()}
                          onClick={() => !isExpanded && setExpandedId(place.id)}
                      >
                          {/* ============ LAYOUT KHI MỞ RỘNG (EXPANDED) ============ */}
                          {isExpanded ? (
                            <div className="relative">
                                {/* 1. Logo/Avatar nhỏ góc phải trên */}
                                <div className={`absolute -top-1 -right-1 w-10 h-10 rounded-full overflow-hidden shadow-md border-2 z-20 
                                  ${theme === 'dark' ? 'border-blue-500' : 'border-blue-100'}`}>
                                  <AvatarImage src={getAvatarImage(place.Image_URLs)} theme={theme} />
                                  <div className="absolute bottom-0 inset-x-0 h-3 bg-black/60 text-[8px] text-white flex items-center justify-center font-bold">
                                    {index + 1}
                                  </div>
                                </div>

                                {/* Nút Xóa (ĐÃ CHUYỂN: Xuống dưới logo) */}
                                <button 
                                    onClick={(e) => handleDelete(place.id, e)}
                                    className={`absolute top-11 right-2 p-1.5 rounded-full transition-colors z-20 
                                      ${theme === 'dark' ? 'text-gray-500 hover:text-red-400 hover:bg-slate-700' : 'text-gray-400 hover:text-red-500 hover:bg-gray-100'}`}
                                    title="Xóa địa điểm"
                                >
                                    <Trash2 size={16} strokeWidth={1.5} />
                                </button>

                                {/* 2. Header Content */}
                                <div className="pr-12 mb-3">
                                    <h3 className={`font-bold text-lg leading-tight mb-1 ${theme === 'dark' ? 'text-blue-400' : 'text-blue-700'}`}>
                                        {place.Name}
                                    </h3>
                                    
                                    {/* Meta info row */}
                                    <div className="flex flex-wrap items-center gap-2 text-xs mb-2">
                                        {place.Rating > 0 && (
                                            <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded ${theme === 'dark' ? 'bg-yellow-900/30 text-yellow-400' : 'bg-yellow-50 text-yellow-600'}`}>
                                                <span className="font-bold">{place.Rating}</span><Star size={10} fill="currentColor" />
                                            </div>
                                        )}
                                        <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded ${theme === 'dark' ? 'bg-slate-700 text-slate-300' : 'bg-gray-100 text-gray-600'}`}>
                                            <Clock size={10} /><span>{place.Opening_Hours}</span>
                                        </div>
                                        {place.Categories && place.Categories.slice(0, 2).map((cat, i) => (
                                            <span key={i} className={`uppercase text-[9px] px-1.5 py-0.5 rounded border font-bold tracking-wide ${theme === 'dark' ? 'border-gray-600 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                                                {cat}
                                            </span>
                                        ))}
                                    </div>

                                    {/* Address */}
                                    <div className={`flex items-start gap-1.5 text-xs ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                                        <MapPin size={12} className="shrink-0 mt-0.5 text-red-500" />
                                        <span className="leading-snug">{place.Address}</span>
                                    </div>
                                </div>

                                {/* 3. Description & Contact */}
                                <div className="space-y-3">
                                    {place.Description && (
                                      <div className={`text-xs italic border-l-2 pl-2 py-1 pr-2 max-h-32 overflow-y-auto custom-scrollbar ${theme === 'dark' ? 'text-gray-400 border-gray-600' : 'text-gray-500 border-gray-300'}`}>
                                        {place.Description}
                                      </div>
                                    )}
                                    
                                    <div className="flex gap-3">
                                        {place.Phone && (
                                            <div className={`flex items-center gap-1.5 text-xs font-medium ${theme === 'dark' ? 'text-green-400' : 'text-green-600'}`}>
                                                <Phone size={12} /><span>{place.Phone}</span>
                                            </div>
                                        )}
                                        {place.Website && (
                                            <a href={place.Website} target="_blank" rel="noreferrer" className={`flex items-center gap-1.5 text-xs font-medium hover:underline ${theme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`}>
                                                <Globe size={12} /><span>Website</span>
                                            </a>
                                        )}
                                    </div>
                                </div>

                                {/* 4. REVIEW CAROUSEL */}
                                {place.Reviews && place.Reviews.length > 0 && (
                                    <ReviewSlider reviews={place.Reviews} theme={theme} />
                                )}

                                {/* 5. Image Gallery */}
                                {validImages.length > 0 && (
                                  <div className="mt-3">
                                    <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar snap-x touch-pan-x">
                                      {validImages.map((imgUrl, idx) => (
                                        <ScheduleImage
                                          key={idx}
                                          src={imgUrl}
                                          theme={theme}
                                          onClick={(e) => openLightbox(imgUrl, e)}
                                          onFinalError={() => handleImageError(imgUrl)}
                                        />
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {/* Nút thu gọn */}
                                <div className="flex justify-center mt-2">
                                    <button 
                                        onClick={(e) => { e.stopPropagation(); setExpandedId(null); }}
                                        className={`text-[10px] uppercase font-bold tracking-widest py-1 px-4 rounded-full transition-colors ${theme === 'dark' ? 'text-gray-500 hover:bg-slate-700 hover:text-gray-300' : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600'}`}
                                    >
                                        ---
                                    </button>
                                </div>
                            </div>
                          ) : (
                            /* ============ LAYOUT KHI THU GỌN ============ */
                            <>
                                <div className={`relative shrink-0 w-12 h-12 rounded-full overflow-hidden shadow-md border-2 ${theme === 'dark' ? 'border-gray-600' : 'border-white'}`}>
                                  <AvatarImage src={getAvatarImage(place.Image_URLs)} theme={theme} />
                                  <div className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-[9px] text-center font-bold">
                                    {index + 1}
                                  </div>
                                </div>

                                <div className="flex-1 flex flex-col overflow-hidden text-right">
                                    <div className="flex items-center justify-end w-full gap-2">
                                        <div className="flex flex-col overflow-hidden flex-1">
                                            <h3 className={`font-bold text-[15px] truncate leading-tight ${theme === 'dark' ? 'text-gray-200' : 'text-gray-700'}`}>
                                                {place.Name}
                                            </h3>
                                            <span className={`text-[10px] truncate mt-0.5 font-medium ${theme === 'dark' ? 'text-gray-200' : 'text-gray-700'}`}>
                                                {place.Address}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <GripVertical size={14} className={`shrink-0 self-center ${theme === 'dark' ? 'text-gray-600' : 'text-gray-300'}`} />
                            </>
                          )}
                      </div>
                  </React.Fragment>
                  );
              })}
              <InsertButton index={places.length} />
          </div>
        )}
      </div>

      {/* Bulk Add Button - Fixed at bottom left */}
      <button
  onClick={() => setShowBulkAdd(!showBulkAdd)}
  // Thêm 'backdrop-blur-sm' vào dòng dưới
  className={`fixed bottom-6 right-40 z-40 p-4 rounded-full shadow-2xl transition-all duration-300 hover:scale-110 backdrop-blur-sm ${
    showBulkAdd
      ? theme === "dark"
        ? "bg-red-600/40 hover:bg-red-700/60" // Thêm /80 (80% rõ)
        : "bg-red-500/40 hover:bg-red-600/60"
      : theme === "dark"
      ? "bg-blue-600/40 hover:bg-blue-700/60" // Thêm /80
      : "bg-blue-500/40 hover:bg-blue-600/60"
  }`}
  title={showBulkAdd ? "Close Bulk Add" : "Open Bulk Add"}
>
  {showBulkAdd ? (
    <X size={24} className="text-white" />
  ) : (
    <Plus size={24} className="text-white" />
  )}
</button>

      {/* Bulk Add Popup */}
      {showBulkAdd && (
        <div className={`fixed bottom-24 left-6 z-40 w-80 rounded-2xl p-4 shadow-2xl border transition-all duration-300 animate-[slideInLeft_0.3s_ease-out] ${
          theme === 'dark' ? 'bg-slate-800 border-blue-500/30' : 'bg-white border-blue-200'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Plus size={18} className="text-blue-500" />
              <h3 className={`font-bold text-sm ${theme === 'dark' ? 'text-gray-200' : 'text-gray-800'}`}>Bulk Add to End</h3>
            </div>
            <button
              onClick={() => setShowBulkAdd(false)}
              className={`p-1 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors`}
            >
              <X size={16} className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} />
            </button>
          </div>
          <div className="space-y-2">
            <input
              type="number"
              min="1"
              max="20"
              value={kCount}
              onChange={(e) => setKCount(e.target.value)}
              placeholder="Enter number of places (1-20)"
              className={`w-full text-sm px-3 py-2 rounded-lg border ${theme === 'dark' ? 'border-slate-700 bg-slate-900 text-gray-100' : 'border-gray-200 bg-white text-gray-800'}`}
            />
            <p className="text-[10px] text-gray-500">System will suggest {kCount || 'k'} places to append at the end</p>
            <button
              onClick={handleAddKPlaces}
              className="w-full text-xs font-semibold px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
              disabled={suggestLoading || !kCount}
            >
              {suggestLoading ? 'Generating...' : 'Generate & Add to End'}
            </button>
          </div>
        </div>
      )}

      {/* Add place wizard */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={closeAddWizard}>
          <div
            className={`w-full max-w-3xl rounded-2xl shadow-2xl p-5 ${theme === 'dark' ? 'bg-slate-900 border border-slate-700 text-gray-100' : 'bg-white border border-gray-200 text-gray-800'}`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-blue-500 font-semibold">Add Destination</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={closeAddWizard} className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800">
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Body collapsible */}
            {showAddModal && (
              <div className="space-y-4">
                {/* Tabs for options */}
                <div className={`rounded-xl border ${theme === 'dark' ? 'border-slate-700 bg-slate-900' : 'border-gray-200 bg-white'}`}>
                  <div className="flex overflow-x-auto custom-scrollbar border-b border-gray-200 dark:border-slate-800">
                    {[
                      { key: 'name', icon: <SearchIcon size={16} /> },
                      { key: 'pos', icon: <GripVertical size={16} /> },
                    ].map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold whitespace-nowrap border-b-2 transition ${
                          activeTab === tab.key
                            ? 'border-blue-500 text-blue-600 dark:text-blue-300'
                            : 'border-transparent text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200'
                        }`}
                      >
                        {tab.icon}
                      </button>
                    ))}
                  </div>

                  <div className="p-4 space-y-2">
                    {activeTab === 'name' && (
                      <div className="space-y-2">
                        <input
                          value={searchName}
                          onChange={(e) => setSearchName(e.target.value)}
                          placeholder="Enter destination name"
                          className={`w-full text-sm px-3 py-2 rounded-lg border ${theme === 'dark' ? 'border-slate-700 bg-slate-900 text-gray-100' : 'border-gray-200 bg-white text-gray-800'}`}
                        />
                        <button
                          onClick={handleSearchByName}
                          className="w-full text-xs font-semibold px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                          disabled={suggestLoading}
                        >
                          {suggestLoading ? 'Searching...' : 'Search'}
                        </button>
                        {/* <p className="text-[11px] text-gray-500">Categories đã chọn sẽ được gửi kèm (tự nối khi call backend).</p> */}
                      </div>
                    )}

                    {activeTab === 'pos' && (
                      <div className="space-y-3">
                        {/* Categories horizontal */}
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <ImageIcon size={16} />
                            <span className="font-semibold text-sm">Suggestion Category</span>
                          </div>
                          <div className="overflow-x-auto pb-2 custom-scrollbar">
                            <div className="flex gap-2 min-w-full">
                              {Array.isArray(categoryOptions) && categoryOptions.map((cat) => (
                                <label
                                  key={cat}
                                  className={`flex items-center gap-2 px-3 py-2 rounded-full border text-sm whitespace-nowrap cursor-pointer ${selectedCategories.includes(cat) ? 'border-blue-500 bg-blue-50 dark:bg-slate-800' : (theme === 'dark' ? 'border-slate-700 bg-slate-900' : 'border-gray-200 bg-white')}`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={selectedCategories.includes(cat)}
                                    onChange={() => toggleCategory(cat)}
                                  />
                                  <span className="font-semibold">{cat}</span>
                                </label>
                              ))}
                              {(!categoryOptions || !categoryOptions.length) && (
                                <span className="text-xs text-gray-500">Loading suggestions...</span>
                              )}
                            </div>
                          </div>
                        </div>

                        <button
                          onClick={handleSuggestByPosition}
                          className="w-full text-xs font-semibold px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                          disabled={suggestLoading}
                        >
                          {suggestLoading ? 'Suggesting...' : 'Suggest'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Result list */}
            <div className={`mt-4 rounded-xl border p-3 ${theme === 'dark' ? 'border-slate-700 bg-slate-900' : 'border-gray-200 bg-white'}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Star size={14} />
                  <span className="font-semibold text-sm">Results</span>
                </div>
                {/* <span className="text-xs text-gray-500">Chọn để thêm vào lịch trình</span> */}
              </div>

              {resultLoading && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading results...
                </div>
              )}

              {!resultLoading && resultPlaces.length === 0 && resultIds.length === 0 && (
                <p className="text-sm text-gray-500">No results yet. Please search or suggest.</p>
              )}

              {!resultLoading && resultPlaces.length === 0 && resultIds.length > 0 && (
                <p className="text-sm text-gray-500">Unable to load details for this result.</p>
              )}

              {!resultLoading && resultPlaces.length > 0 && (
                <div className="relative group -mx-3">
                  {/* Left navigation button */}
                  <button
                    onClick={() => scrollResultList('left')}
                    className={`absolute left-2 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity ${theme === 'dark' ? 'bg-slate-700 text-white hover:bg-slate-600' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
                  >
                    <ChevronLeft size={20} />
                  </button>

                  {/* Right navigation button */}
                  <button
                    onClick={() => scrollResultList('right')}
                    className={`absolute right-2 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity ${theme === 'dark' ? 'bg-slate-700 text-white hover:bg-slate-600' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
                  >
                    <ChevronRight size={20} />
                  </button>

                  <div ref={resultScrollRef} className="overflow-x-auto pb-2 scrollbar-hide px-3 snap-x snap-mandatory">
                    <div className="flex gap-3">
                      {resultPlaces.map((place) => {
                        const checked = selectedIds.includes(place.rowid);
                        const badge = place.Categories?.[0] || 'Place';
                        const imgSrc = getAvatarImage(place.Image_URLs);
                        return (
                          <div
                            key={place.rowid}
                            className={`w-64 shrink-0 snap-start rounded-xl border overflow-hidden cursor-pointer transition shadow-sm hover:shadow-md ${checked ? 'border-blue-500 ring-2 ring-blue-200 dark:ring-blue-900' : (theme === 'dark' ? 'border-slate-700' : 'border-gray-200')} ${theme === 'dark' ? 'bg-slate-800' : 'bg-white'}`}
                            onClick={() => setSelectedIds((prev) => checked ? prev.filter(v => v !== place.rowid) : [...prev, place.rowid])}
                          >
                            {/* Image header */}
                            <div className="relative h-32 w-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                              <AvatarImage src={imgSrc} theme={theme} />
                              <div className="absolute top-2 right-2">
                                <input
                                  type="checkbox"
                                  checked={checked}
                                  onChange={() => setSelectedIds((prev) => checked ? prev.filter(v => v !== place.rowid) : [...prev, place.rowid])}
                                  onClick={(e) => e.stopPropagation()}
                                  className="w-5 h-5 cursor-pointer"
                                />
                              </div>
                              <div className="absolute top-2 left-2">
                                <div className="text-xs px-2 py-1 rounded-full bg-blue-600 text-white font-semibold shadow-md">{badge}</div>
                              </div>
                            </div>
                            
                            {/* Content */}
                            <div className="p-3 space-y-2">
                              <div>
                                <p className={`text-sm font-bold line-clamp-2 leading-tight ${theme === 'dark' ? 'text-gray-100' : 'text-gray-800'}`}>{place.Name}</p>
                                <p className="text-[11px] text-gray-500 truncate mt-1">{place.Address}</p>
                              </div>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1 text-[11px]">
                                  <Star size={12} fill="currentColor" className="text-amber-400" />
                                  <span className="font-semibold text-amber-600 dark:text-amber-400">{place.Rating || '—'}</span>
                                </div>
                                <div className="flex gap-1 text-[10px]">
                                  {place.Categories?.slice(1,3).map((c) => (
                                    <span key={c} className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300">{c}</span>
                                  ))}
                                </div>
                              </div>
                              <button
                                onClick={(e) => handlePreviewPlace(place, e)}
                                className="w-full text-xs font-semibold px-3 py-1.5 rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:from-green-600 hover:to-emerald-700 transition-all flex items-center justify-center gap-1.5"
                              >
                                <MapPin size={12} />
                                Preview on Map
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-end mt-3 gap-2">
                {/* <button
                  onClick={closeAddWizard}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold border ${theme === 'dark' ? 'border-slate-700 text-gray-200 hover:bg-slate-800' : 'border-gray-200 text-gray-700 hover:bg-gray-100'}`}
                >
                  Cancel
                </button> */}
                <button
                  onClick={handleApplySelected}
                  className="px-4 py-2 rounded-lg text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                  disabled={suggestLoading}
                >
                  Add to schedule
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default Schedule;