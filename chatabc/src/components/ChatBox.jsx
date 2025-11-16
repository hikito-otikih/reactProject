import React, { useEffect } from 'react'
import { useAppContext } from '../context/AppContext'
import { assets } from '../assets/assets';
import Message from './message';
import toast from 'react-hot-toast';

const ChatBox = () => {
  const {selectedChat, theme, axios, user, token, fetchUserChats} = useAppContext();
  const [message, setMessage] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  
  const containerRef = React.useRef(null);

  const [prompt, setPrompt] = React.useState('');
  const [mode, setMode] = React.useState('text');
  // const [isPublished, setIsPublished] = React.useState(false);

  const onsubmit = async (e) => {
    try {
      e.preventDefault();
      if (!user) return;
      setLoading(true);
      const promptcopy = prompt;
      setPrompt('');
      setMessage(prev => [...prev, {role: 'user', content: promptcopy, timestamp: new Date()}]);
      const {data} = await axios.post('/api/message/text', { chatID : selectedChat._id, prompt }
        , { headers: { Authorization: token} });
      if (data.success) {
        setMessage(prev => [...prev, data.reply]);
        fetchUserChats();
        setPrompt(promptcopy);
      }
      else {
        toast.error(data.message || "Failed to send message");
      }
    } catch (error) {
      toast.error("Failed to send message");
    } finally {
      setLoading(false);
      setPrompt('');
    }
  }

  useEffect(() => {
    if (selectedChat) {
      setMessage(selectedChat.messages);
    }
  }, [selectedChat]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [message]);

  return (
    
    <div className='h-full flex flex-col justify-between p-5 md:p-10 xl:px-30 max-md:pt-14 2xl:pr-40'>      {/* chat div */}
      <div ref={containerRef} className='flex-1 mb-5 overflow-y-scroll'>
        {message.length === 0 && (
          <div className='h-full flex flex-col items-center justify-center gap-2 text-primary'>
            <img src={theme === 'dark' ? assets.logo_full : assets.logo_full_dark} alt='' className='w-full max-w-56 sm:max-w-68' />
            <p className='mt-5 text-4xl sm:text-6xl text-center text-gray-400 dark:text-white'>Ask me anything.</p>
          </div>
        )}
        {message.map((msg, index) => <Message key={index} message={msg} />)}
        {/*Three dots loading animation */}
        {
          loading && <div className='loader flex items-center gap-1.5'>
            <div className='w-1.5 h-1.5 bg-gray-500 dark:bg-white rounded-full animate-bounce'></div>
            <div className='w-1.5 h-1.5 bg-gray-500 dark:bg-white rounded-full animate-bounce'></div>
            <div className='w-1.5 h-1.5 bg-gray-500 dark:bg-white rounded-full animate-bounce'></div>
          </div>
        }
      </div>
          {/* {mode == 'image' && (
            <label className='inline-flex items-center gap-2 mb-3 text-sm mx-auto'>
              <p className='text-xs'>Publish to Community</p>
              <input type="checkbox" checked={isPublished} onChange={() => setIsPublished(!isPublished)} />
            </label>
          )} */}

      {/*prompt input div */}
      <form onSubmit={onsubmit} className='flex items-center gap-2 p-3 border border-gray-300 dark:border-white/15 rounded-md'>
        <select className='text-sm p-l3 pr-2 outline-none' value={mode} onChange={(e) => setMode(e.target.value)}>
          <option className='dark:bg-purple-900' value="text">Text</option>
          {/* <option className='dark:bg-purple-900' value="image">Image</option> */}
        </select>
        <input onChange={(e)=>setPrompt(e.target.value)}
          value={prompt}
          type='text'
          placeholder='Type your prompt here...'
          className='flex-1 w-full text-sm outline-none' required />
          <button disabled={loading}>
            <img src={loading ? assets.stop_icon : assets.send_icon} alt="" className='w-8 cursor-pointer'/>
          </button>
      </form>
    </div>
  )
}

export default ChatBox
