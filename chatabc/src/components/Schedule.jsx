import React, { useState, useRef } from 'react';
import { MapPin, Clock, GripVertical, Trash2, Plus, Image as ImageIcon, X } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const Schedule = () => {
  // Dữ liệu mẫu (Giữ nguyên)
  const initialData = [
    { 
      id: 1, 
      Name: "Lotte Cinema", 
      Address: "235, Nguyễn Văn Cừ, Q.1", 
      Categories: ["Cinema", "Entertainment"], 
      Image_URLs: ["https://lh3.googleusercontent.com/p/AF1QipMS3iuTWiTevezicptNIMlsP8UCk5liK7yz279I=s0", "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSyn2lYOFmxzKGB233L-6sJfce2qitkECz85CCELNoH1b29Ir4IXZASwNHAr87nd--qCCywx5q2iv6T_b9vWTL6xU_2dLXv_hGH43Yh8KZecvNMlBLzXjiNAq7Sy8F7Eg4HOSbWD=s0", "//:0"],
      Opening_Hours: "08:00 - 24:00"
    },
    { 
      id: 2, 
      Name: "GS25", 
      Address: "Nguyễn Văn Cừ, Q.5", 
      Categories: ["Convenience"], 
      Image_URLs: ["https://lh3.googleusercontent.com/gps-cs-s/AG0ilSw2FIuNyImkgwIevvtGyQWtYUMLoaWz_mnDiRfqtviCHeiOFPxBIprbuCxMrp99CMcaxYSQ7eaqtfRUufB_ALAXejbuYAVbJdDlCRNWw6KZtmEYtST5vxzGX6Ix2_hZVaMi7dQdqd5Q2-WL=s0", "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSz6jZpNdP33Lff4JIlf7oc_JG6TQxhfI6tcicTolqKF3fVz7NXKaZv72DPE2AQutGcH8tsPK1mfKxgGI2nJXFrHXxsCI_Yd6PZKnPe9SfQ7U95wubvwwHwFaY8rIpl1g-nlxmYpz_7Rj-37=s0", "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSxgsMf8XE1uniAPFxk7rnfphu1uXo6dwPUJLiL2djGXtuqp640O-BcXGkeUv6GOdNZkK1Z0FR1VS-KxrCLRakdTz7zxt3ku_vHqJSjlEJTnXFV631OQkU0gh6EI3H1nDZ2vqlXW5CEUBz9Y=s0"],
      Opening_Hours: "24/7"
    },
    { 
      id: 3, 
      Name: "Nhà Hàng Út Cà Mau", 
      Address: "512 Nguyễn Thị Minh Khai", 
      Categories: ["Restaurant", "Vietnamese"], 
      Image_URLs: ["https://lh3.googleusercontent.com/gps-cs-s/AG0ilSwpV0z1cbrTCKNwqdjiFbl_hm68FybUOtubPQTGZV9XCn3fumFOF9BAamTgvgBQqfEHBi1dy_34gmOZU6RhtOlUbQYfy2U2hLkTTPx0e3PZf-7c6yxsttYSiL2OrBnatPTbp5RfiKCccqKC=s0", "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSwYUrslzZtw-dCton8nAK8qYAEWJJDCgmkx8h5WoXruxsMv9hLs-VS0PYUbO1XjzfBzpZdr9MSKz1m8CCkr8DHlSOfjDtMzcGnxuG7oBF5eplzSYoKaZaU6hHCTbmaGRDz_gxoynA=s0", "https://lh3.googleusercontent.com/p/AF1QipMHZR41AbKTfEFifLOJTHg-xP1kCR8MDBcKmiUb=s0"],
      Opening_Hours: "10:00 - 23:00"
    },
    { 
      id: 4, 
      Name: "Hotel Nikko Saigon", 
      Address: "235 Nguyễn Văn Cừ", 
      Categories: ["Luxury Hotel"], 
      Image_URLs: ["https://lh3.googleusercontent.com/gps-cs-s/AG0ilSyYowm9JnHYgNmQ9sXM6WXdgEX75menCrEeWjXIpOwunQlxOaZ3qqCeSGC7y8TJavb2_IS-z9zG1zvmce-XybzIGTR6GqKm3mhg1NGMMJtPhS7a7ddNLwlIuNqQRMFkGkYcK5KStsK4m7hv=s0", "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSybR6JAeETafbvLCN_6VfR3Ey_8oQvQaLWaptRRy8HnlsZIwFT3VYB8Ge-UvQ_E7GYkcz4aGeUUTydLtuFUqbBxtgKPUBfTmueXBlLqhzqPeslwvXtpAQOSlpYP2kbeaqrqjYE=s0", "//:0"],
      Opening_Hours: "Open 24h"
    },
    { 
      id: 5, 
      Name: "Chợ Đũi", 
      Address: "Lý Thái Tổ, Q.10", 
      Categories: ["Market", "Local"], 
      Image_URLs: ["https://lh3.googleusercontent.com/gps-cs-s/AG0ilSyB3_eGmsi8XmD5Ur-wr2Rxj3PwBIVRNYOroZUphkEo8hyfQjRzhJ3CxGJiy0-X03JcfIgbPJ8XhYuDBOFjHP9lYTYkm_y6l4h22dr_Ar3ca3VNpOmS8mGXillUkWdotgrSdMuy=s0", "//:0", "//:0"], 
      Opening_Hours: "06:00 - 18:00"
    }
  ];

  const [places, setPlaces] = useState(initialData);
  const [expandedId, setExpandedId] = useState(null);
  const { selectedImage, setSelectedImage } = useAppContext();
  
  const dragItem = useRef(null);
  const dragOverItem = useRef(null);

  const getValidImages = (urls) => {
    if (!urls || !Array.isArray(urls)) return [];
    return urls.filter(url => url && url.startsWith('http'));
  };

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
  };

  const handleInsert = (index) => {
    const newPlace = {
      id: Date.now(),
      Name: "New Location",
      Address: "Address...",
      Categories: ["Custom"],
      Image_URLs: [],
      Opening_Hours: "--:--"
    };
    const newPlaces = [...places];
    newPlaces.splice(index, 0, newPlace);
    setPlaces(newPlaces);
  };

  const handleDelete = (id, e) => {
    e.stopPropagation();
    setPlaces(places.filter(item => item.id !== id));
  };

  const openLightbox = (imgUrl, e) => {
    e.stopPropagation();
    setSelectedImage(imgUrl);
  };

  const closeLightbox = () => {
    setSelectedImage(null);
  };

  // Component tái sử dụng cho nút Insert (để dùng cho cả đầu list và cuối list)
  const InsertButton = ({ index }) => (
    <div 
      className="group/insert h-6 -my-3 mr-[3.5rem] flex flex-row-reverse items-center cursor-pointer opacity-0 hover:opacity-100 transition-opacity duration-200 z-10"
      onClick={() => handleInsert(index)}
    >
      {/* Đường kẻ ngang: Đậm hơn (h-[3px]) và màu xanh rõ hơn để dễ nhìn */}
      <div className="w-full h-[3px] bg-blue-500 shadow-sm relative flex flex-row-reverse items-center rounded-full">
        {/* Nút bấm Insert: Màu đậm hơn */}
        <div className="absolute right-0 bg-blue-600 text-white text-[10px] font-bold px-3 py-1 rounded-full flex items-center gap-1 shadow-md border border-white hover:scale-105 transition-transform">
          <Plus size={10} strokeWidth={4}/> <span>Thêm điểm đến</span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          height: 6px !important;
          display: block !important;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.5); 
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #94a3b8;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background-color: #64748b;
          cursor: grab;
        }
      `}</style>

      <div className='h-full flex flex-col p-4 pt-10 relative overflow-y-auto overflow-x-hidden bg-transparent'>
        
        {/* Timeline Line */}
        <div className="absolute right-[2.15rem] top-0 bottom-0 w-[3px] bg-gray-400/60 border-l border-dashed border-gray-500/50 z-0"></div>

        <div className="relative flex flex-col gap-5 pb-20 w-full z-10">
          
          {places.map((place, index) => {
            const isExpanded = expandedId === place.id;
            const validImages = getValidImages(place.Image_URLs);

            return (
              <React.Fragment key={place.id}>
                {/* 1. Insert Area (Trước mỗi item) */}
                <InsertButton index={index} />

                {/* 2. MAIN CARD */}
                <div
                  className={`
                    relative z-10 flex flex-row-reverse items-start gap-3 cursor-pointer group/item
                    transition-all duration-300 ease-out
                    ${isExpanded ? 'my-2' : ''}
                  `}
                  draggable
                  onDragStart={(e) => (dragItem.current = index)}
                  onDragEnter={(e) => (dragOverItem.current = index)}
                  onDragEnd={handleSort}
                  onDragOver={(e) => e.preventDefault()}
                  onClick={() => setExpandedId(isExpanded ? null : place.id)}
                >
                  
                  {/* Avatar Tròn: Thêm viền trắng dày + bóng đổ để tách khỏi Map */}
                  <div className={`
                    relative shrink-0 w-12 h-12 rounded-full overflow-hidden shadow-lg bg-white border-[3px] 
                    transition-all duration-300 z-20
                    ${isExpanded 
                      ? 'border-blue-600 scale-110 shadow-xl' // Khi mở: Viền xanh đậm
                      : 'border-white group-hover:border-gray-200'} // Khi đóng: Viền trắng
                  `}>
                    <img 
                      src={getAvatarImage(place.Image_URLs)} 
                      alt={place.Name}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute bottom-0 inset-x-0 bg-black/70 text-white text-[9px] text-center font-bold">
                      {index + 1}
                    </div>
                  </div>

                  {/* Content Box: Thay đổi màu nền/viền để nổi bật trên Map trắng */}
                  <div className={`
                    flex-1 rounded-xl transition-all duration-300 bg-white
                    ${isExpanded 
                      ? 'shadow-2xl border-2 border-blue-500' // KHI MỞ: Viền xanh đậm bao quanh
                      : 'shadow-[0_2px_10px_rgba(0,0,0,0.15)] border border-gray-300 hover:border-blue-400 hover:shadow-xl'} // KHI ĐÓNG: Viền xám, bóng đậm hơn
                  `}>
                    
                    {/* Header */}
                    <div className={`flex items-center justify-between w-full px-3 py-2.5 ${isExpanded ? 'border-b border-gray-100' : ''}`}>
                      {!isExpanded && <GripVertical size={14} className="text-gray-400 shrink-0 mr-2" />}
                      
                      <div className="flex flex-col overflow-hidden flex-1 text-right">
                        <h3 className={`font-bold text-[15px] truncate leading-tight ${isExpanded ? 'text-gray-900' : 'text-gray-800'}`}>
                          {place.Name}
                        </h3>
                        {!isExpanded && (
                          <span className="text-[10px] text-gray-500 truncate mt-0.5 font-medium">{place.Address}</span>
                        )}
                      </div>

                      {isExpanded && (
                        <button 
                          onClick={(e) => handleDelete(place.id, e)}
                          className="text-gray-400 hover:text-red-500 p-1.5 rounded-full hover:bg-red-50 transition-colors ml-2"
                        >
                          <Trash2 size={14} strokeWidth={1.5} />
                        </button>
                      )}
                    </div>

                    {/* Details Expanded */}
                    <div className={`
                      overflow-hidden transition-all duration-500 ease-in-out
                      ${isExpanded ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}
                    `}>
                      <div className="p-3 pt-2 space-y-3">
                        <div className="flex flex-col gap-2 text-xs text-gray-600">
                          <div className="flex items-center justify-end gap-1.5 text-right">
                             <span className="truncate font-medium">{place.Address}</span>
                             <MapPin size={12} className="text-red-500 shrink-0"/>
                          </div>
                          <div className="flex justify-end">
                            <div className="flex items-center gap-1 shrink-0 bg-blue-50 px-2 py-1 rounded border border-blue-100 w-fit">
                              <span className="font-bold text-blue-700">{place.Opening_Hours}</span>
                              <Clock size={11} className="text-blue-500"/>
                            </div>
                          </div>
                        </div>

                        {validImages.length > 0 && (
                          <div className="w-full">
                            <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar snap-x touch-pan-x flex-row-reverse">
                              {validImages.map((imgUrl, idx) => (
                                <img 
                                  key={idx}
                                  src={imgUrl}
                                  alt="img"
                                  className="h-16 w-16 rounded-lg object-cover border border-gray-200 shadow-sm hover:shadow-md hover:scale-105 transition-all cursor-zoom-in snap-start shrink-0 bg-gray-50"
                                  onClick={(e) => openLightbox(imgUrl, e)}
                                />
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex gap-1.5 flex-wrap justify-end">
                          {place.Categories && place.Categories.map((cat, i) => (
                            <span key={i} className="text-[9px] uppercase tracking-wide bg-gray-100 text-gray-600 px-2 py-0.5 rounded-[4px] border border-gray-200 font-bold">
                              {cat}
                            </span>
                          ))}
                        </div>

                      </div>
                    </div>
                  </div>
                </div>
              </React.Fragment>
            );
          })}
          
          {/* 3. Insert Area Cuối cùng (Thay thế nút + to) */}
          <InsertButton index={places.length} />

        </div>
      </div>
    </>
  )
}

export default Schedule;