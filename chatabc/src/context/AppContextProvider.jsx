import { useEffect, useCallback } from "react";
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

    const value = {
        // navigate, user, setUser, chats, setChats, selectedChat, setSelectedChat, theme, setTheme
        navigate, user, setUser, chats, setChats, selectedChat, setSelectedChat, theme, setTheme, createNewChat, loadingUser, fetchUser, token, setToken, axios, fetchUserChats, setChatsListChanged
    };
    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    )
}

// export const useAppContext = () => useContext(AppContext);