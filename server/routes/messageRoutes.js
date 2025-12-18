import express from 'express';
import { protect } from '../middlewares/auth.js';
import { textMessageController, newSequenceMessageController, get_suggest_category, getSearchByName } from '../controllers/messageController.js';
import { getSuggestAround, getSuggestForPosition, getSuggestItineraryToSequence, addKPlaces, newStartPositionController } from '../controllers/messageController.js';


const messageRoutes = express.Router();
messageRoutes.post('/text', protect, textMessageController);
messageRoutes.post('/newSequence', protect, newSequenceMessageController);
messageRoutes.post('/newStartPosition', protect, newStartPositionController);
messageRoutes.get('/getSuggestCategory', protect, get_suggest_category);
messageRoutes.get('/getSearchByName', getSearchByName);
messageRoutes.get('/getSuggestAround', protect, getSuggestAround);
messageRoutes.get('/getSuggestForPosition', protect, getSuggestForPosition);
messageRoutes.get('/getSuggestItineraryToSequence', protect, getSuggestItineraryToSequence);
messageRoutes.get('/addKPlaces', protect, addKPlaces);

export default messageRoutes;