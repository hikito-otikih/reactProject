import express from 'express';
import { getUser, registerUser, loginUser } from '../controllers/userController.js';
import { protect } from '../middlewares/auth.js';

const userRoutes = express.Router();

userRoutes.post('/register', registerUser);
userRoutes.post('/login', loginUser);
userRoutes.get('/data', protect, getUser);

export default userRoutes;