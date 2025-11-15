import express from 'express';
import { protect } from '../middlewares/auth.js';
import { textMessageController } from '../controllers/messageController.js';

const messageRoutes = express.Router();
messageRoutes.post('/text', protect, textMessageController);

export default messageRoutes;