import React, { useState, useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import SideBar from './components/SideBar'
import ChatBox from './components/ChatBox'
import { assets } from './assets/assets'
import './assets/prism.css'
import Loading from './pages/Loading'
import { useAppContext } from './context/AppContext'
import Login from './pages/Login'
import { Toaster } from 'react-hot-toast';
import RoutineMap from './components/RoutineMap.jsx'; 
import Schedule from './components/Schedule.jsx';
import ShowImage from './components/showImage.jsx';

const App = () => {
  const {user, loadingUser} = useAppContext();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const {pathname} = useLocation();
  
  const [isWidgetOpen, setIsWidgetOpen] = useState(true);
  const [activeRoutine, setActiveRoutine] = useState(null); 
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  
  const ChevronLeft = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
  );
  const ChevronRight = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
  );

  if (pathname === '/loading' || loadingUser) return <Loading />;

  return (
    <>
      <Toaster />
      
      {user ? (
        <div className="flex h-screen w-screen overflow-hidden bg-gray-50 dark:bg-[#1a1a1a]">
          
          {/* --- 2. CỘT TRÁI: CHAT BOX --- (Giữ nguyên) */}
          <div 
            className={`
              flex-shrink-0 h-full bg-white dark:bg-[#1a1a1a] border-r border-gray-200 dark:border-gray-800
              transition-[width,transform] duration-500 ease-in-out z-20 overflow-hidden relative
              ${isWidgetOpen ? 'w-full md:w-[420px]' : 'w-0 border-none'}
            `}
          >
            <div className="w-screen md:w-[420px] md:min-w-[420px] h-full flex flex-col relative">
                {!isMenuOpen && (
                   <img src={assets.menu_icon} className='absolute top-3 left-3 w-8 h-8 cursor-pointer not-dark:invert z-50' onClick={() => setIsMenuOpen(true)} alt="menu"/>
                )}

                  {isWidgetOpen && !isMenuOpen && (
                    <button
                      onClick={() => setIsScheduleOpen(prev => !prev)}
                      title={isScheduleOpen ? 'Close Schedule' : 'Open Schedule'}
                      className="absolute top-3 left-[370px] w-8 h-8 md:w-10 md:h-10 flex items-center justify-center bg-white text-black dark:bg-[#2d2d2d] dark:text-white rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 z-50 hover:opacity-90 transition-opacity"
                      style={{ transition: 'left 0.5s ease-in-out' }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    </button>
                )}

                <div className='flex h-full w-full relative'>
                  <SideBar isMenuOpen={isMenuOpen} setIsMenuOpen={setIsMenuOpen} />
                  <div className={`flex-1 w-full h-full ${isMenuOpen ? 'hidden md:block' : 'block'}`}>
                    <Routes>
                      <Route path="/" element={<ChatBox onShowMap={setActiveRoutine}/>} />
                    </Routes>
                  </div>
                </div>
            </div>
          </div>

          {/* --- 3. CỘT PHẢI: MAP & SCHEDULE --- */}
          {/* Thay đổi: Bỏ 'flex', giữ 'relative' để làm mốc tọa độ */}
          <div className="flex-1 h-full relative z-10 bg-gray-100 overflow-hidden">

             {/* LAYER 1: MAP (Nằm dưới cùng, chiếm toàn màn hình) */}
             <div className="absolute inset-0 w-full h-full z-0">
               <RoutineMap 
                  routineData={activeRoutine} 
                  onClose={() => setActiveRoutine(null)} 
               />
             </div>

             {/* LAYER 2: NÚT TOGGLE CHAT (Nổi lên trên Map) */}
             <div className="absolute top-1/2 -translate-y-1/2 left-0 z-30">
                <button 
                  onClick={() => {
                    setIsWidgetOpen(!isWidgetOpen);
                    setIsScheduleOpen(false); // Đóng schedule khi mở rộng map để tránh rối
                  }}
                  className="
                    flex items-center justify-center
                    bg-white dark:bg-[#2d2d2d] 
                    text-gray-700 dark:text-white 
                    w-6 h-12 md:w-8 md:h-16
                    rounded-r-xl 
                    shadow-lg border border-l-0 border-gray-200 dark:border-gray-700 
                    hover:bg-gray-50 dark:hover:bg-[#3d3d3d]
                    transition-colors cursor-pointer
                  "
                > 
                  {isWidgetOpen ? <ChevronLeft /> : <ChevronRight />} 
                </button> 
             </div>

            {/* LAYER 3: SCHEDULE PANEL (Trong suốt hoàn toàn) */}
            <div 
              className={`
                absolute top-0 right-0 h-full z-20 
                transition-all duration-500 ease-in-out
                ${isScheduleOpen ? 'w-[350px] translate-x-0' : 'w-0 translate-x-full opacity-0'}
              `}
            >
              {/* Container: bg-transparent để nhìn thấu Map */}
              <div className="w-[350px] min-w-[350px] h-full flex flex-col relative bg-transparent">
                
                {/* Nút đóng Schedule: Làm nổi bật hơn chút vì nền trong suốt */}
                <div className="absolute top-3 right-3 z-50">
                  <button
                    onClick={() => setIsScheduleOpen(false)}
                    className="w-9 h-9 flex items-center justify-center rounded-full bg-white text-gray-700 shadow-md hover:bg-red-50 hover:text-red-500 transition-all active:scale-95"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                  </button>
                </div>

                <Schedule />
              </div>
            </div>

          </div>
          
          <ShowImage />
        </div>
      ) : (
        <div className='bg-gradient-to-b from-[#242124] to-[#000000] h-screen w-screen flex items-center justify-center'>
          <Login />
        </div>
      )}
    </>
  )
}

export default App