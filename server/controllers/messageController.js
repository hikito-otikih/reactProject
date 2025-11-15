import Chat from "../models/Chat.js";
import { openai } from "../configs/openai.js";

export const textMessageController = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, prompt} = req.body;
        const chat = await Chat.findOne({ _id: chatID, userID });
        chat.messages.push({ role: "user", content: prompt, timestamp: Date.now()});
        const {choices} = await openai.chat.completions.create({
            model: "gemini-2.0-flash",
            messages: [
                {
                    role: "user",
                    content: prompt,
                },
            ],
        });
        const reply = {...choices[0].message, timestamp: Date.now()};
        chat.messages.push(reply);
        await chat.save();
        res.json({ "success": true, "data": reply });
    } catch (error) {
        return res.json({ "success": false, "message": error.message, prompt: req.body.prompt });
    }
};