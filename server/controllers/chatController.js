import Chat from '../models/Chat.js';
export const createChat  = async (req, res) => {
    try {
        const userID = req.user._id;
        const chatData = {
            userID, 
            messages: [],
            name: "New Chat",
            userName: req.user.username
        }
        await Chat.create(chatData);
        res.json({ "success": true, "message": "Chat created successfully" });
    } catch (error) {
        return res.json({ "success": false, "message": error.message });
    }
}

export const getChats  = async (req, res) => {
    try {
        const userID = req.user._id;
        const chats = await Chat.find({ userID }).sort({ createdAt: -1 });
        res.json({ "success": true, chats });
    } catch (error) {
        return res.json({ "success": false, "message": "Error fetching chats" });
    }
}

export const deleteChat  = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID} = req.body
        await Chat.deleteOne({ _id: chatID, userID });
        res.json({ "success": true, "message": "Chat deleted successfully" });
    } catch (error) {
        return res.json({ "success": false, "message": "Error fetching chats" });
    }
}