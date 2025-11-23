import mongoose from "mongoose";

const chatSchema = new mongoose.Schema({
    userID : {type : String, ref : 'User', required: true},
    userName : {type : String, required: true},
    name : {type : String, required: true},
    messages: [
        {
            role : { type: String, required: true },
            content : { type: String, required: true },
            timestamp :  { type: Number, required: true },
            originJson : { type: mongoose.Schema.Types.Mixed } // Lưu trữ dữ liệu gốc từ Gemini API
        }
    ]
}, { timestamps: true });

const Chat = mongoose.model("Chat", chatSchema);

export default Chat;