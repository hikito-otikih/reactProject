import { useEffect, useCallback, use } from "react";
import { dummyChats, dummyUserData } from "../assets/assets";
import { createContext, useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { AppContext } from "./AppContext.jsx";

axios.defaults.baseURL = import.meta.env.VITE_SERVER_URL;

export const AppContextProvider = ({ children }) => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [chats, setChats] = useState([]);
    const [selectedChat, setSelectedChat] = useState(null);
    const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
    const [token, setToken] = useState(() => localStorage.getItem("token") || null);
    //const [token, setToken] = useState(localStorage.getItem('token') || null);
    const [loadingUser, setLoadingUser] = useState(false);
    const [chatsListChanged, setChatsListChanged] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
    const [startPosition, setStartPosition] = useState(null);
    const [schedulePlaces, setSchedulePlaces] = useState([]);
    const [showPreviewLocation, setShowPreviewLocation] = useState([]);

    // const fetchUserChats = useCallback(async () => {
    //     if (!token) return; 
    //     try {
    //         const {data} = await axios.get('/api/chat/get', {headers: {Authorization : token}});
    //         if (data.success) {
    //             setChats(data.chats);
    //             if (data.chats.length > 0) {
    //                 setSelectedChat(data.chats[0]);
    //             } else {
    //                 setSelectedChat(null); 
    //             }
    //             return data.chats; 
    //         } else {
    //             toast.error("Failed to fetch user chats");
    //         }
    //     } catch (error) {
    //         toast.error("Failed to fetch user chats");
    //     }
    //     return []; 
    // }, [token]); 

    const fetchUserChats = useCallback(async () => {
        if (!token) return; 
            try {
                const {data} = await axios.get('/api/chat/get', {headers: {Authorization : token}});
                //console.log("Fetched chats data:", data);
                if (data.success) {
                    setChats(data.chats);
                    if (data.chats.length > 0) {
                        setSelectedChat(data.chats[0]);
                    } else {
                        setSelectedChat(null); 
                    }
                    return data.chats; 
                } else {
                    toast.error("Failed to fetch user chats");
                }
            } catch (error) {
                toast.error("Failed to fetch user chats");
            }
      return []; 
    }, [token]); 
    const fetchUser = useCallback(async () => {
        if (!token) { 
          setLoadingUser(false);
          setUser(null);
          return;
        }
        try {
            const { data } = await axios.get('/api/user/data', {headers: {Authorization : token}});
            if (data.success) {
                setUser(data.user);
            }
            else {
                toast.error(data.message);
                setToken(null); 
                localStorage.removeItem("token");
            }
        }
        catch (error) {
            toast.error(error.message + " Please try again.");
            setToken(null); 
            localStorage.removeItem("token");
        }
        finally {
            setLoadingUser(false);
        }
    }, [token]);
    const createNewChat = useCallback(async () => {
        if (!token) return toast.error("Login to create a new chat"); 
        try {
            navigate('/');
            await axios.get('/api/chat/create', {headers: {Authorization : token}});
            await fetchUserChats(); 
        } catch (error) {
            toast.error(error.message + " Please try again.");
        }
    }, [token, navigate, fetchUserChats]);
    useEffect(() => {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } 
        else {
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem('theme', theme);
    }, [theme])
    useEffect(() => {
        const loadAndCheckChats = async () => {
            const fetchedChats = await fetchUserChats();
            console.log("Fetched chats:", fetchedChats);
            if (fetchedChats && fetchedChats.length === 0) {
                try {
                    navigate('/');
                    await axios.get('/api/chat/create', {headers: {Authorization : token}});
                    await fetchUserChats(); 
                } catch (error) {
                    toast.error(error.message + " Please try again.");
                }
            }
        };

        if (user && token) { 
            loadAndCheckChats();
        }
        else {
            setChats([])
            setSelectedChat(null)
        }
    }, [user, token, navigate, fetchUserChats, chatsListChanged]);
    useEffect(() => {
        console.log("useEffect token:", token);
        if (token) {
            setLoadingUser(true);
            fetchUser();
        }
        else {
            setLoadingUser(false);
            setUser(null);
        }
    }, [token, fetchUser])


   useEffect(() => {
        // --- 1. Xử lý Start Coordinate ---
        if (selectedChat && selectedChat.start_coordinate) {
            // Kiểm tra mảng và độ dài >= 2
            if (Array.isArray(selectedChat.start_coordinate) && selectedChat.start_coordinate.length >= 2) {
                const lat = parseFloat(selectedChat.start_coordinate[0]);
                const lon = parseFloat(selectedChat.start_coordinate[1]);
                
                if (!isNaN(lat) && !isNaN(lon)) {
                    setStartPosition({
                        lat,
                        lon,
                        name: selectedChat.start_coordinate_name || "Unknown Location"  
                    });
                } else {
                    console.warn("Invalid coordinates values:", selectedChat.start_coordinate);
                    setStartPosition(null);
                }
            } else {
                // Nếu mảng rỗng [] hoặc thiếu phần tử, set null để tránh lỗi
                setStartPosition(null);
            }
        } else {
            setStartPosition(null);
        }

        // --- 2. Xử lý Fetch Schedule Places ---
        const fetchSchedulePlaces = async () => {
            // ✅ SỬA LỖI 1: Kiểm tra thêm điều kiện mảng rỗng (length === 0)
            if (!selectedChat || !selectedChat.sequence || selectedChat.sequence.length === 0) {
                setSchedulePlaces([]); 
                return; // Dừng ngay, không gọi API nữa
            }

            try {
                // ✅ SỬA LỖI 2: Bọc trong try/catch để bắt lỗi 400/500 từ server
                const response = await axios.post('/api/static_db/query', {
                    list_id: selectedChat.sequence
                });

                const safeParseList = (str) => {
                    if (!str) return [];
                    try {
                        return JSON.parse(str);
                    } catch (e) {
                        return str.replace(/[\[\]]/g, '').split(',').map(s => s.trim()).filter(s => s !== "");
                    }
                };

                if (response.data && Array.isArray(response.data.data)) {
                    const formattedData = response.data.data.map((item, index) => {
                        let parsedCategories = safeParseList(item.categories);
                        if (parsedCategories.length === 0) parsedCategories = ["Place"];

                        let parsedImages = safeParseList(item.images);
                        
                        let parsedReviews = [];
                        try { if (item.reviews) parsedReviews = JSON.parse(item.reviews); } catch (e) {}
                        
                        let hoursObj = {};
                        try { if (item.openingHours) hoursObj = JSON.parse(item.openingHours); } catch (e) {}

                        const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
                        const displayHours = hoursObj[today] || "Checking...";

                        return {
                            rowid: item.rowid,
                            id: item.id || Date.now() + index,
                            Name: item.name || item.title || item.address?.split(',')[0] || "Unknown",
                            Address: item.address || "",
                            Categories: parsedCategories,
                            Image_URLs: parsedImages,
                            Opening_Hours: displayHours,
                            Rating: item.rating || 0,
                            Phone: item.phone,
                            Website: item.website,
                            Description: item.description_en || item.description,
                            Reviews: parsedReviews,
                            Lat: item.location_lat,
                            Lon: item.location_lon
                        };
                    });
                    
                    setSchedulePlaces(formattedData);
                    console.log("Fetched schedule places:", formattedData);
                }
            } catch (error) {
                console.error("Error fetching schedule places:", error);
                setSchedulePlaces([]); // Fallback về mảng rỗng nếu lỗi
            }
        };

        fetchSchedulePlaces();
    }, [selectedChat]);

    useEffect(() => {
        // Reset preview locations when chat or user changes
        setShowPreviewLocation([]);
    }, [selectedChat, user, token]);

    const value = {
        // navigate, user, setUser, chats, setChats, selectedChat, setSelectedChat, theme, setTheme
        navigate, user, setUser, chats, setChats, selectedChat, setSelectedChat, theme, setTheme, createNewChat, loadingUser, fetchUser, token, setToken, axios, fetchUserChats, setChatsListChanged, selectedImage, setSelectedImage, startPosition, setStartPosition, schedulePlaces, setSchedulePlaces, showPreviewLocation, setShowPreviewLocation
    };
    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    )
}

// export const useAppContext = () => useContext(AppContext);