import React, { useEffect } from 'react'
import { assets } from '../assets/assets'
import moment from 'moment'
import Markdown from 'react-markdown'
import Prism from 'prismjs'

// Thêm onSave và onSaveAndDisplay vào props
const Message = ({ message, onDisplay, onSuggestionClick, onShowPlaceDetails, onPreviewOnMap, onAddToSchedule, placeDetails }) => {
  
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

            {/* Suggestion Questions */}
            {message.suggestions && message.suggestions.length > 0 && (
              <div className='mt-3 ml-1'>
                <p className='text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium'>You might also ask:</p>
                <div className='flex flex-col gap-2'>
                  {message.suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => onSuggestionClick && onSuggestionClick(suggestion)}
                      className='text-left p-2.5 px-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-700 dark:to-gray-800 border border-blue-200 dark:border-gray-600 rounded-lg text-xs text-gray-700 dark:text-gray-200 hover:shadow-md hover:border-blue-400 dark:hover:border-purple-500 transition-all duration-200 hover:-translate-y-0.5'
                    >
                      <span className='flex items-center gap-2'>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3.5 h-3.5 text-blue-500">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
                        </svg>
                        {suggestion}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Database Results - Suggested Locations */}
            {message.database_results && message.database_results.length > 0 && (
              <div className='mt-3 ml-1'>
                <p className='text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium'>Suggested Locations:</p>
                <div className='grid grid-cols-1 gap-2'>
                  {message.database_results.map((placeId, idx) => {
                    const place = placeDetails?.[placeId];
                    return (
                      <div
                        key={idx}
                        className='flex items-center justify-between p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-all duration-200'
                      >
                        {/* Clickable Place Details Panel */}
                        <div 
                          onClick={() => onShowPlaceDetails && onShowPlaceDetails(placeId, place)}
                          className='flex items-start gap-3 flex-1 min-w-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 -m-3 p-3 rounded-lg transition-colors'
                        >
                          {/* Place Image/Icon */}
                          <div className='flex-shrink-0 w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg overflow-hidden shadow-sm'>
                            {(place?.Image_URLs?.[0] || place?.images?.[0]) ? (
                              <img 
                                src={place.Image_URLs?.[0] || place.images?.[0]} 
                                alt={place?.name || place?.Name} 
                                className='w-full h-full object-cover'
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'flex';
                                }}
                              />
                            ) : null}
                            <div className={`w-full h-full flex items-center justify-center ${(place?.Image_URLs?.[0] || place?.images?.[0]) ? 'hidden' : 'flex'}`}>
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-8 h-8 text-white">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                              </svg>
                            </div>
                          </div>
                          
                          {/* Place Details */}
                          <div className='flex-1 min-w-0'>
                            <h4 className='text-sm font-semibold text-gray-800 dark:text-gray-100 truncate'>
                              {place?.name || place?.Name || 'Loading...'}
                            </h4>
                            {(place?.address || place?.Address) && (
                              <p className='text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5'>
                                {place.address || place.Address}
                              </p>
                            )}
                            {place?.rating && (
                              <div className='flex items-center gap-1 mt-1'>
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3 text-yellow-500">
                                  <path fillRule="evenodd" d="M10.868 2.884c-.321-.772-1.415-.772-1.736 0l-1.83 4.401-4.753.381c-.833.067-1.171 1.107-.536 1.651l3.62 3.102-1.106 4.637c-.194.813.691 1.456 1.405 1.02L10 15.591l4.069 2.485c.713.436 1.598-.207 1.404-1.02l-1.106-4.637 3.62-3.102c.635-.544.297-1.584-.536-1.65l-4.752-.382-1.831-4.401z" clipRule="evenodd" />
                                </svg>
                                <span className='text-xs text-gray-600 dark:text-gray-300'>{place.rating}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className='flex-shrink-0 ml-2 flex flex-col gap-1'>
                          {/* Preview on Map Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onPreviewOnMap && onPreviewOnMap(placeId, place);
                            }}
                            className='p-1.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-md transition-all duration-200 shadow-sm hover:shadow-md flex items-center justify-center'
                            title='Preview on Map'
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                            </svg>
                          </button>

                          {/* Add to Schedule Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onAddToSchedule && onAddToSchedule(placeId, place);
                            }}
                            className='p-1.5 bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white rounded-md transition-all duration-200 shadow-sm hover:shadow-md flex items-center justify-center'
                            title='Add to Schedule'
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

          </div>
        </div>
      )
      }   
    </div>
  )
}

export default Message