import React, { useEffect, useRef, useState } from 'react'
import { useAppContext } from '../context/AppContext'
import { assets } from '../assets/assets';
import Message from './Message';
import toast from 'react-hot-toast';

const ChatBox = ({ onShowMap }) => {
  const {selectedChat, theme, axios, user, token} = useAppContext();
  const [message, setMessage] = useState([]);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);
  const [prompt, setPrompt] = useState('');

  // --- 1. XỬ LÝ AUTO SCROLL (Thêm mới) ---
  // Chạy mỗi khi 'message' hoặc 'loading' thay đổi
  useEffect(() => {
    if (containerRef.current) {
      // Scroll xuống đáy container
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
      if (!prompt.trim()) return; // Chặn gửi tin nhắn rỗng
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
         <div className="flex flex-col gap-4">
            {message.map((msg, index) => (
                <Message 
                    key={index} 
                    message={msg} 
                    onDisplay={() => handleDisplayMap(msg)} 
                />
            ))}

            {/* --- 2. HIỂU ỨNG LOADING (Thêm mới) --- */}
            {loading && (
              <div className="flex items-start gap-2.5">
                 {/* Avatar AI (giả sử dùng assets.gemini_icon hoặc logo của bạn) */}
                 <img src={assets.gemini_icon} className="w-8 h-8 rounded-full p-1 border border-gray-200" alt="AI" />
                 
                 {/* Bong bóng loading */}
                 <div className="flex flex-col w-full max-w-[320px] leading-1.5 p-4 border-gray-200 bg-gray-100 rounded-e-xl rounded-es-xl dark:bg-[#2d2d2d]">
                    <div className="flex space-x-2 justify-center items-center">
                        <div className='h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]'></div>
                        <div className='h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]'></div>
                        <div className='h-2 w-2 bg-gray-400 rounded-full animate-bounce'></div>
                    </div>
                 </div>
              </div>
            )}
         </div>
      </div>
      
      {/* Input Form */}
      <form onSubmit={onsubmit} className='flex items-center gap-2 p-2 px-4 bg-gray-100 dark:bg-[#2d2d2d] rounded-3xl shadow-sm border border-transparent focus-within:border-gray-300 dark:focus-within:border-gray-600 transition-all'>
         <input 
            onChange={(e)=>setPrompt(e.target.value)} 
            value={prompt} 
            type='text' 
            placeholder='Type a message...' 
            className='flex-1 bg-transparent outline-none dark:text-white' 
         />
         <button disabled={loading || !prompt.trim()} className={`p-2 rounded-full text-white transition-all ${loading || !prompt.trim() ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}>
             <img src={assets.send_icon} className='w-4 h-4 invert' alt="send" />
         </button>
      </form>
    </div>
  )
}

export default ChatBox