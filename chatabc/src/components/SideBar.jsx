import React from 'react'
import { useAppContext } from '../context/AppContext'
import { assets } from '../assets/assets'
import { useState } from 'react'
import moment from "moment"
import toast from 'react-hot-toast'
import { Token } from 'prismjs'

const SideBar = ({isMenuOpen, setIsMenuOpen}) => {
  const { chats, setSelectedChat, theme, setTheme, user, navigate, createNewChat, axios, setChats, setUserChats, setToken, token , fetchUserChats, setChatsListChanged} = useAppContext()
  const [search, setSearch] = useState('')
  const logout = () => {
    setToken(null);
    localStorage.removeItem("token");
    toast.success("Logged out successfully");
  }
  const deleteChat = async(e, chatId) => {
    try {
      e.stopPropagation();
      const confirm = window.confirm("Are you sure you want to delete this chat?");
      if (!confirm) return;
      console.log("Deleting chat with ID:", chatId);
      const {data} = await axios.post('/api/chat/delete', {chatID : chatId}, {
        headers: {
          Authorization: token
        }
      });
      if (data.success) {
        setChats(prev => prev.filter(chat => chat._id !== chatId));
        console.log("Chat deleted:", data);
        //await fetchUserChats();
        toast.success("Chat deleted successfully");
        setChatsListChanged(prev => !prev);
      }
    } catch (error) {
      toast.error(error.messages || "Failed to delete chat");
    }
  }
  return (
    <div className={`
      flex flex-col h-full w-full p-5 
      bg-white dark:bg-[#171717] 
      dark:text-white  /* <--- THÊM DÒNG NÀY */
      border-r border-gray-200 dark:border-[#444]
      transition-transform duration-300 ease-in-out
      absolute left-0 top-0 z-20 
      ${!isMenuOpen ? '-translate-x-full' : 'translate-x-0'}
    `}>
    {/* </div><div className={`flex flex-col h-full w-full p-5 dark:bg-gradient-to-b from-[#242124]/30 to-[#000000]/30 border-r border-[#80609F]/30 backdrop-blur-3xl trasition-all duration-500 absolute left-0 z-1 ${!isMenuOpen ? '-translate-x-full' : 'translate-x-0'}`}> */}
        {/* logo */}
        <img src={theme === 'dark' ? assets.logo_full : assets.logo_full_dark} alt="" className='w-full max-w-48'/>
        {/* new chat button */}
        <button onClick={createNewChat} className='flex justify-center items-center w-full py-2 mt-10 text-white bg-gradient-to-r from-[#A456F7] to-[#3D81F6] text-sm rounded-md cursor-pointer'>
          <span className='mr-2 text-xl'>+</span> New Chat
        </button>
        {/* search conversation */}
        <div className='flex items-center gap-2 p-3 mt-4 border border-gray-400 dark:border-white/20 rounded-md'>
          <img src={assets.search_icon} className='w-4 not-dark:invert' alt=''/>
          {/* <input value={search} onChange={(e) => setSearch(e.target.value)} className='text-xs placeholder:text-gray-400 outline-none' type='text' placeholder='Search...' /> */}
          <input 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
            className='text-xs placeholder:text-gray-400 outline-none bg-transparent dark:text-white' /* <--- THÊM bg-transparent và dark:text-white */
            type='text' 
            placeholder='Search...' 
          />
        </div>
        {/* conversation list */}
        <div className="flex-1 overflow-y-auto my-4 space-y-2 pr-2">
          {chats.length > 0 && <p className='mt-4 text-sm text-gray-500 dark:text-gray-400'>Conversations</p>}
          <div>
              {
                chats.filter((chat)=>chat.messages[0] ? chat.messages[0].content.toLowerCase().includes(search.toLowerCase()) : chat.name.toLowerCase().includes(search.toLowerCase())).map((chat) =>(
                  <div onClick={() => {navigate('/'); setSelectedChat(chat); setIsMenuOpen(false)}} key={chat._id} className='p-2 px-4 dark:bg-[#57317C]/10 border border-gray-300 dark:border-[#80609F]/15 rounded-md cursor-pointer flex justify-between group'>
                    <div>
                      <p className='truncate w-full'>
                        {chat.messages.length > 0 ? chat.messages[0].content.slice(0, 32) : chat.name}
                      </p>
                      <p className='text-xs text-gray-500 dark:text-[#B1A6C0]'>
                        {moment(chat.updatedAt).fromNow()}
                      </p>
                    </div>
                    <img src={assets.bin_icon} className='block md:hidden md:group-hover:block w-4 cursor-pointer not-dark:invert'
                    alt='' onClick={e => toast.promise(deleteChat(e, chat._id), {loading: 'deleting ...'})} />
                  </div>
                ))
              }
          </div>
        </div>
      {/* theme toggle button */}
      <div className='flex items-center justify-between gap-2 p-3 mt-4 border border-gray-300 dark:border-white/15 rounded-md'>
          <div className='flex items-center gap-2 text-sm'>
            <img src={assets.theme_icon} className='w-4.5 not-dark:invert' alt='' />
            <p>Dark Mode</p>
          </div>
          <label className='relative inline-flex cursor-pointer'>
            <input onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} type='checkbox' className='sr-only peer' checked={theme === 'dark'} />
            <div className='w-9 h-5 bg-gray-400 rounded-full peer-checked:bg-purple-600 transition-all'>
            </div>
            <span className='absolute left-1 top-1 w-3 h-3 bg-white rounded-full transition-transform peer-checked:translate-x-4'></span>
          </label>
      </div>
      {/* user profile */}
      <div className='flex items-center gap-3 p-3 mt-3 border border-gray-300 dark:border-white/15 rounded-md cursor-pointer group'>
        <img src={assets.user_icon} className='w-7 rounded-full' alt='' />
        <p className='flex-1 text-sm dark:text-primary truncate'>{user ? user.username : 'Login your account'}</p>
        {user && <img onClick={logout} src={assets.logout_icon} className='w-4 cursor-pointer not-dark:invert group-hover:block' alt='' />}
      </div>
      <img onClick={() => setIsMenuOpen(false)} src={assets.close_icon} className='absolute top-3 right-3 w-5 h-5 cursor-pointer not-dark:invert' alt='' />
    </div>
  )
}

export default SideBar
