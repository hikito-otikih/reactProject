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
            suggestions: [{ type: String, required: false }], 
            database_results: [{ type: Number, required: false }]
        }
    ],
    start_coordinate:[{ type: Number, required: false }],
    sequence: [{ type: Number, required: false }],
    start_coordinate_name: { type: String, required: false }
}, { timestamps: true });

const Chat = mongoose.model("Chat", chatSchema);

export default Chat;

const convertChatSchemaToJson = (chatData) => {
    const data = chatData.toObject ? chatData.toObject() : chatData;

    return {
        history: {
            responses: data.messages.map(({ role, content, timestamp, ...rest }) => ({
                whom: role,       
                message: content, 
                ...rest           
            }))
        },
        start_coordinate: data.start_coordinate,
        sequence: data.sequence
    };
};
export { convertChatSchemaToJson };