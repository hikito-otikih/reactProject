import React, { useState, useEffect } from 'react' // SỬA LẠI: import { useState }
import Community from './pages/Community'
import { Route, Routes, useLocation } from 'react-router-dom'
import SideBar from './components/SideBar'
import Credits from './pages/Credits'
import ChatBox from './components/ChatBox'
import { assets } from './assets/assets'
import './assets/prism.css'
import Loading from './pages/Loading'
import { useAppContext } from './context/AppContext'
import Login from './pages/Login'
import { Toaster } from 'react-hot-toast';
// Đảm bảo đường dẫn import đúng
import RoutineMap from './components/RoutineMap.jsx'; 

const App = () => {
  const {user, loadingUser} = useAppContext();
  const [isMenuOpen, setIsMenuOpen] = useState(false); // Dùng useState trực tiếp cho ngắn gọn
  const {pathname} = useLocation();
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);

  // State này quyết định việc hiển thị Map
  const [activeRoutine, setActiveRoutine] = useState(null); 
  
  useEffect(() => {
    // Đóng menu khi thay đổi route
    console.log("activeRoutine changed:", activeRoutine);
  }, [activeRoutine]);
  
  const ChatIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
  );
  const CloseIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
  );

  if (pathname === '/loading' || loadingUser) return <Loading />;

  return (
    <>
      <Toaster />
        
        {user ? (
          <>
            {/* Map luôn được render ở background */}
            {/* Khi activeRoutine = null, nó chỉ hiện bản đồ trống */}
            <RoutineMap 
               routineData={activeRoutine} 
               onClose={() => setActiveRoutine(null)} 
            />

            {/* Nút mở Widget chat */}
            <div className="fixed bottom-5 right-6 z-50 flex-col items-end"> 
              <button onClick={() => setIsWidgetOpen(!isWidgetOpen)} className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-300 hover:scale-110 flex items-center justify-center" > 
                {isWidgetOpen ? <CloseIcon /> : <ChatIcon />} 
              </button> 
            </div>

            {/* Khung Chat Widget */}
            <div
            className={`
              fixed z-40 overflow-hidden shadow-2xl
              transition-all duration-300 ease-in-out
              
              inset-0 w-full h-full rounded-none
              
              md:inset-auto md:bottom-24 md:right-6
              md:w-[400px] md:h-[600px]
              md:rounded-2xl md:border md:border-gray-800
              
              ${!isWidgetOpen
                ? 'opacity-0 pointer-events-none translate-y-10 scale-95'
                : 'opacity-100 pointer-events-auto translate-y-0 scale-100'
              }`}>
              {!isMenuOpen && <img src={assets.menu_icon} className='absolute top-3 left-3 w-8 h-8 cursor-pointer not-dark:invert z-50' onClick={() => setIsMenuOpen(true)} alt="menu"/>}
              <div className='dark:bg-[#1a1a1a] bg-white h-full w-full flex flex-col rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-800'>
                <div className='flex h-full w-full relative'>
                  <SideBar isMenuOpen={isMenuOpen} setIsMenuOpen={setIsMenuOpen} />
                  
                  <div className={`flex-1 w-full h-full ${isMenuOpen ? 'hidden md:block' : 'block'}`}>
                    <Routes>
                      {/* Truyền hàm setActiveRoutine xuống để ChatBox gọi khi bấm nút */}
                      <Route path="/" element={<ChatBox onShowMap={setActiveRoutine}/>} />
                    </Routes>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className='bg-gradient-to-b from-[#242124] to-[#000000] h-screen w-screen flex items-center justify-center'>
            <Login />
          </div>
        )}
    </>
  )
}

export default App