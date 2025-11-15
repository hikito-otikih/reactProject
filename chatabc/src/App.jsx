import React, { use } from 'react'
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

const App = () => {
  const {user} = useAppContext();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const {pathname} = useLocation();
  if (pathname === '/loading') return <Loading />;
  return (
    <>
      {!isMenuOpen && <img src={assets.menu_icon} className='absolute top-3 left-3 w-8 h-8 cursor-pointer md:hidden not-dark:invert' onClick={() => setIsMenuOpen(true)} />}
      {user ? (
        <div className='dark:bg-gradient-to-b from-[#242124] to-[#000000] dark:text-white'>
        <div className='flex h-screen w-screen'>
          <SideBar isMenuOpen={isMenuOpen} setIsMenuOpen={setIsMenuOpen} />
          <div className="flex-1 w-full overflow-y-auto">
            <Routes>
              <Route path="/" element={<ChatBox />} />
              {/* <Route path="/credits" element={<Credits />} />
              <Route path="/community" element={<Community />} /> */}
            </Routes>
          </div>
        </div>
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
