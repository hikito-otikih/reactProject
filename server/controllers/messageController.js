import Chat from "../models/Chat.js";
import { openai } from "../configs/openai.js";
import axios from "axios";

export const textMessageController = async (req, res) => {
    try {
        const userID = req.user._id;
        const {chatID, prompt} = req.body;
        const chat = await Chat.findOne({ _id: chatID, userID });
        chat.messages.push({ role: "user", content: prompt, timestamp: Date.now()});

        let aiResponseContent = "";
        let isScheduleResponse = false;

        // 2. Gọi qua Python Service (Scheduling Service)
        try {
            const pythonServiceUrl = process.env.SCHEDULING_SERVICE || "http://127.0.0.1:5000";
            
            // Gửi request POST sang Python
            const pythonRes = await axios.post(`${pythonServiceUrl}/analyze`, {
                input: prompt
            });

            // Kiểm tra xem Python có trả về lịch trình hợp lệ không
            // (Giả sử Python trả về JSON, nếu có key 'error' nghĩa là thất bại)
            if (pythonRes.data && !pythonRes.data.error) {
                // Thành công! Lấy kết quả từ Python
                // Chúng ta chuyển JSON thành string để lưu vào MongoDB (vì field content thường là string)
                // Hoặc bạn có thể lưu raw JSON nếu schema DB cho phép.
                aiResponseContent = JSON.stringify(pythonRes.data); 
                isScheduleResponse = true;
            }
        } catch (pythonError) {
            // Nếu Python service chưa bật hoặc lỗi kết nối, chỉ cần log ra và fallback về Gemini
            console.log("Python service skipped or error:", pythonError.message);
        }
        console.log("schedule response:", aiResponseContent);
        let newPromt = prompt;
        if (isScheduleResponse) {
            newPromt = `You are a travel assistant. 
            I will give you a trip schedule in JSON format. 
            Your task is to convert it into a clear, friendly, human-readable trip description. 
            Preserve all information from the JSON. 
            Organize the text by day, in chronological order.
            Write in a concise, easy-to-understand style.
            Expand short labels into natural sentences (e.g., “check_in”: “Check in at the hotel”).
            If times exist, include them naturally in the text.
            If locations or activities are missing details, still render them gracefully.
            Do not include any JSON or code in your output—only the formatted text.
            Here is the JSON trip schedule: ${aiResponseContent}`;
        } else {
            newPromt = `You are a travel assistant.
            Tell the client about the error in their trip request, suggest they try again, and provide helpful guidance.
            Here is the user's original request: ${prompt}`;
        }
        const {choices} = await openai.chat.completions.create({
            model: "gemini-2.0-flash",
            messages: [
                {
                    role: "user",
                    content: newPromt,
                },
            ],
        });
        const reply = {...choices[0].message, timestamp: Date.now(), originJson: isScheduleResponse ? aiResponseContent : null};
        chat.messages.push(reply);
        await chat.save();
        res.json({ "success": true, "reply": reply });
    } catch (error) {
        return res.json({ "success": false, "message": error.message, prompt: req.body.prompt });
    }
};