import React from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css'; // Bắt buộc phải import CSS của Leaflet

const Map = () => {
  // Tọa độ mặc định (Ví dụ: TP. Hồ Chí Minh)
  const position = [10.7769, 106.7009];

  return (
    <div className="fixed inset-0 w-full h-full -z-10">
      <MapContainer 
        center={position} 
        zoom={13} 
        scrollWheelZoom={true} // Tắt lăn chuột để zoom
        zoomControl={false}     // Tắt nút +/- zoom
        dragging={true}        // Tắt kéo thả map
        doubleClickZoom={false} // Tắt double click
        attributionControl={false} // Ẩn dòng bản quyền (tùy chọn)
        maxZoom={18}
        minZoom={8}
        className="w-full h-full outline-none"
      >
        {/* Layer bản đồ cơ bản */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Mẹo: Thêm lớp phủ mờ (overlay) để text bên trên dễ đọc hơn */}
        {/* Nếu bạn dùng Dark Mode, có thể dùng CartoDB Dark Matter thay thế URL trên:
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" 
        */}
      </MapContainer>

      {/* Lớp phủ gradient để làm mờ map, giúp nội dung đè lên dễ đọc hơn */}
      <div className="absolute inset-0 bg-white/30 dark:bg-black/60 backdrop-blur-[2px] pointer-events-none"></div>
    </div>
  );
};

export default Map;