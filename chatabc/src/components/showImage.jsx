import React from 'react'
import { useAppContext } from '../context/AppContext'
import { X } from 'lucide-react'

const ShowImage = () => {
    const { selectedImage, setSelectedImage } = useAppContext();

    const closeLightbox = (e) => {
        if (e && e.stopPropagation) e.stopPropagation();
        setSelectedImage(null);
    };

    if (!selectedImage) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-[#0B1120]/95 backdrop-blur-sm p-6 animate-fadeIn"
            onClick={closeLightbox}
        >
            <button
                className="absolute top-5 right-5 text-white/50 hover:text-white transition-colors z-10"
                onClick={closeLightbox}
            >
                <X size={32} strokeWidth={1} />
            </button>
            <img
                src={selectedImage}
                alt="Full"
                className="max-w-full max-h-full object-contain rounded-lg shadow-2xl animate-zoomIn pointer-events-auto"
                onClick={(e) => e.stopPropagation()}
            />
        </div>
    );
}

export default ShowImage