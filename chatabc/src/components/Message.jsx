import React, { useEffect } from 'react'
import { assets } from '../assets/assets'
import moment from 'moment'
import Markdown from 'react-markdown'
import Prism from 'prismjs'

// Thêm onSave và onSaveAndDisplay vào props
const Message = ({ message, onDisplay }) => {
  
  useEffect(() => {
    Prism.highlightAll();
  }, [message.content]);

  return (
    <div className='w-full'>
      {message.role === 'user' ? (
        // --- USER MESSAGE ---
        <div className='flex items-end justify-end gap-2 mb-3'>
           <div className='flex flex-col items-end max-w-[85%]'>
              {/* Thêm break-words để sửa lỗi tràn lề */}
              <div className='p-3 px-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-2xl rounded-tr-none shadow-md text-sm leading-relaxed break-words overflow-hidden'>
                {message.content}
              </div>
              <span className='text-[10px] text-gray-400 mt-1 mr-1'>{moment(message.timestamp).format('h:mm A')}</span>
           </div>
           <img src={assets.user_icon} className='w-6 h-6 rounded-full mb-4 object-cover border border-gray-200' alt='User' />
        </div>
      )
      : 
      (
        // --- AI MESSAGE ---
        <div className='flex items-start gap-2 mb-3'>
          <div className='flex-shrink-0 mt-1'>
             <img src={assets.gemini_icon || assets.logo_icon} className='w-6 h-6 rounded-full p-0.5 bg-white border' alt='AI' /> 
          </div>
          
          <div className='flex flex-col max-w-[90%]'>
            {/* Bong bóng chat AI */}
            <div className='p-3 px-4 bg-white dark:bg-[#2d2d2d] border border-gray-100 dark:border-gray-700 rounded-2xl rounded-tl-none shadow-sm text-sm text-gray-800 dark:text-gray-200 leading-relaxed overflow-hidden'>
                {message.isImage ? (
                  <img src={message.content} className='w-full rounded-md' alt='' />
                ) : (
                  <div className='markdown-content'>
                    <Markdown>{message.content}</Markdown>
                  </div>
                )} 
            </div>

            {/* Footer: Timestamp và Các nút hành động */}
            <div className='flex items-center justify-between mt-1 ml-1 gap-4'>
                {/* Timestamp */}
                <span className='text-[10px] text-gray-400'>
                    {moment(message.timestamp).format('h:mm A')}
                </span>

                {/* Nút Hiển thị bản đồ nếu có originJson */}
                {message.originJson && (
                  <div className='flex gap-2'>
                      <button 
                          onClick={() => onDisplay && onDisplay(message)}
                          className='flex items-center gap-1 text-[10px] font-medium text-white bg-purple-600 hover:bg-purple-700 px-2 py-1 rounded-md transition-colors shadow-sm'
                          title="Lưu và hiển thị ngay"
                      >
                          {/* Icon Eye/Play nhỏ */}
                          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                          </svg>
                          Visualize the Schedule
                      </button>
                  </div>
                )}
            </div>

          </div>
        </div>
      )
      }   
    </div>
  )
}

export default Message