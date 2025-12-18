import React, { useEffect, useState } from 'react'
import { useAppContext } from '../context/AppContext'
import { X, AlertCircle } from 'lucide-react'

const buildProxyUrl = (url) => `https://images.weserv.nl/?url=${encodeURIComponent(url)}`;

const ShowImage = () => {
    const { selectedImage, setSelectedImage } = useAppContext();
    const [currentSrc, setCurrentSrc] = useState(selectedImage);
    const [triedProxy, setTriedProxy] = useState(false);
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        setCurrentSrc(selectedImage);
        setTriedProxy(false);
        setFailed(false);
    }, [selectedImage]);

    const closeLightbox = (e) => {
        if (e && e.stopPropagation) e.stopPropagation();
        setSelectedImage(null);
        setFailed(false);
        setCurrentSrc(null);
        setTriedProxy(false);
    };

    const handleError = () => {
        if (!triedProxy && selectedImage) {
            setTriedProxy(true);
            setCurrentSrc(buildProxyUrl(selectedImage));
            return;
        }
        setFailed(true);
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

            {failed ? (
                <div className="flex flex-col items-center justify-center gap-4 bg-red-900/20 border border-red-500/50 rounded-lg p-8 text-center max-w-md text-white">
                    <AlertCircle size={48} className="text-red-400" />
                    <div>
                        <p className="font-semibold mb-2">Không thể tải ảnh</p>
                        <p className="text-red-200 text-sm mb-4 break-all">{selectedImage}</p>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                window.open(selectedImage, '_blank');
                            }}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                        >
                            Mở link gốc
                        </button>
                    </div>
                </div>
            ) : (
                <img
                    src={currentSrc}
                    alt="Full"
                    referrerPolicy="no-referrer"
                    className="max-w-full max-h-full object-contain rounded-lg shadow-2xl animate-zoomIn pointer-events-auto"
                    onClick={(e) => e.stopPropagation()}
                    onError={handleError}
                    onLoad={() => console.log('Ảnh tải thành công:', currentSrc)}
                />
            )}
        </div>
    );
}

export default ShowImage