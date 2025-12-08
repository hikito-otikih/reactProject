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
  const {selectedChat, theme, axios, user, token} = useAppContext();
  const [message, setMessage] = useState([]);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);
  const [prompt, setPrompt] = useState('');

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
    </div>
  )
}

export default ChatBox