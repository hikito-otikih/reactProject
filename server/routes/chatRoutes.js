import express from 'express';
import { createChat, getChats, deleteChat } from '../controllers/chatController.js';
import { protect } from '../middlewares/auth.js';

const chatRoutes = express.Router();

chatRoutes.get('/create', protect, createChat);
chatRoutes.get('/get', protect, getChats);
chatRoutes.post('/delete', protect, deleteChat);

export default chatRoutes;