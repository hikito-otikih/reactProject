import Chat from "../models/Chat.js";
import { openai } from "../configs/openai.js";
import axios from "axios";
import { convertChatSchemaToJson } from "../models/Chat.js";

export const textMessageController = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, prompt} = req.body;
        const chat = await Chat.findOne({ _id: chatID, userID });
        const historyForAI = convertChatSchemaToJson(chat);
        console.log("History for AI:", JSON.stringify(historyForAI, null, 2));
        chat.messages.push({ role: "user", content: prompt, timestamp: Date.now()});

        let aiResponseContent = "";
        let isScheduleResponse = false;
        try {
            const pythonServiceUrl = process.env.SCHEDULING_SERVICE || "http://127.0.0.1:5000";
            
            const pythonRes = await axios.post(`${pythonServiceUrl}/api/process-input`, {
                history: historyForAI,
                input: prompt
            });
            if (pythonRes.success === false) {
                throw new Error(pythonRes.message || "Python service returned an error");
            }
            if (pythonRes.data && !pythonRes.data.error) {
                aiResponseContent = JSON.stringify(pythonRes.data); 
                aiResponseContent = JSON.parse(aiResponseContent).data;
                isScheduleResponse = true;
            }
        } catch (pythonError) {
            console.log("Python service skipped or error:", pythonError.message);
        }
        console.log("schedule response:", aiResponseContent);
        const reply = {content: aiResponseContent.message, timestamp: Date.now(), role: "bot", suggestions: aiResponseContent.suggestions || [], database_results: aiResponseContent.database_results || []};
        chat.messages.push(reply);
        await chat.save();
        res.json({ "success": true, "reply": reply });
    } catch (error) {
        return res.json({ "success": false, "message": error.message, prompt: req.body.prompt });
    }
};

export const newSequenceMessageController = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, sequence} = req.body;
        const chat = await Chat.findOne({ _id: chatID, userID });
        chat.sequence = sequence;
        await chat.save();
        res.json({ "success": true , "sequence": chat.sequence });
    } catch (error) {
        return res.json({ "success": false, "message": error.message});
    }
};

export const newStartPositionController = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, start_coordinate, start_coordinate_name} = req.body;
        const chat = await Chat.findOne({ _id: chatID, userID });
        chat.start_coordinate = start_coordinate;
        chat.start_coordinate_name = start_coordinate_name;
        await chat.save();
        res.json({ "success": true , "startPosition": chat.start_coordinate, "startPositionName": chat.start_coordinate_name });
    }
    catch (error) {
        return res.json({ "success": false, "message": error.message});
    }
};

export const get_suggest_category = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID} = req.query;
        const chat = await Chat.findOne({ _id: chatID, userID });
        const pythonServiceUrl = process.env.SCHEDULING_SERVICE || "http://127.0.0.1:5000";
        const pythonRes = await axios.get(`${pythonServiceUrl}/api/get-suggest-category`, {
            params: {
                history: convertChatSchemaToJson(chat)
            }
        });
        console.log("Suggest categories response:", pythonRes.data);
        res.json({ "success": true , "categories": pythonRes.data });
    } catch (error) {
        return res.json({ "success": false, "message": error.message});
    }
}

export const getSearchByName = async (req, res) => {
    try {
        const {name, exact = true, limit = 10} = req.query;
        const pythonServiceUrl = process.env.SCHEDULING_SERVICE || "http://127.0.0.1:5000";
        const pythonRes = await axios.get(`${pythonServiceUrl}/api/search-by-name`, {
            params: {
                name,
                exact,
                limit
            }
        });
        console.log("Search by name response:", pythonRes.data);
        res.json({ "success": true , "results": pythonRes.data });
    } catch (error) {
        return res.json({ "success": false, "message": error.message});
    }
};

export const getSuggestForPosition = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, position, category, limit} = req.query;
        const chat = await Chat.findOne({ _id: chatID, userID });
        const pythonServiceUrl = process.env.SCHEDULING_SERVICE || "http://127.0.0.1:5000";
        const pythonRes = await axios.get(`${pythonServiceUrl}/api/suggest-for-position`, {
            params: {
                history: convertChatSchemaToJson(chat),
                position,
                category,
                limit
            }
        });
        //console.log("history for suggest for position:", JSON.stringify(convertChatSchemaToJson(chat), null, 2));
        //console.log("Suggest for position response:", pythonRes.data);
        res.json({ "success": true , "suggestions": pythonRes.data });
    } catch (error) {
        return res.json({ "success": false, "message": error.message});
    }
};

export const getSuggestItineraryToSequence = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, limit} = req.query;
        const chat = await Chat.findOne({ _id: chatID, userID });
        const pythonServiceUrl = process.env.SCHEDULING_SERVICE || "http://127.0.0.1:5000";
        const pythonRes = await axios.get(`${pythonServiceUrl}/api/suggest-itinerary-to-sequence`, {
            params: {
                history: convertChatSchemaToJson(chat),
                limit
            }
        });
        console.log("Suggest itinerary to sequence response:", pythonRes.data);
        res.json({ "success": true , "suggestions": pythonRes.data });
    } catch (error) {
        return res.json({ "success": false, "message": error.message});
    }   
};

export const getSuggestAround = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, lat, lon, limit, category} = req.query;
        const chat = await Chat.findOne({ _id: chatID, userID });
        const pythonServiceUrl = process.env.SCHEDULING_SERVICE || "http://127.0.0.1:5000";
        const pythonRes = await axios.get(`${pythonServiceUrl}/api/suggest-around`, {
            params: {
                history: convertChatSchemaToJson(chat),
                lat,
                lon,
                limit,
                category
            }
        });
        console.log("Suggest around response:", pythonRes.data);
        res.json({ "success": true , "suggestions": pythonRes.data });
    } catch (error) {
        return res.json({ "success": false, "message": error.message});
    }
};

export const addKPlaces = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, limit} = req.query;
        const chat = await Chat.findOne({ _id: chatID, userID });
        const pythonServiceUrl = process.env.SCHEDULING_SERVICE || "http://127.0.0.1:5000";
        const pythonRes = await axios.get(`${pythonServiceUrl}/api/suggest-itinerary-to-sequence`, {
            params: {
                history: convertChatSchemaToJson(chat),
                limit
            }
        });
        console.log("Add K places response:", pythonRes.data);
        res.json({ "success": true , "suggestions": pythonRes.data });
    } catch (error) {
        return res.json({ "success": false, "message": error.message});
    }
}