import User from '../models/User.js';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';

const generateToken = (id) => {
    return jwt.sign({ id }, process.env.JWT_SECRET, {
        expiresIn: '30d',
    });
}

export const registerUser = async (req, res) => {
    const { username, email, password } = req.body;
    try {
        const userExist = await User.findOne({ email });
        if (userExist) {
            return res.json({"success": false, "message": "User already exists"});
        }
        const user = await User.create({ username, email, password });
        const token = generateToken(user._id);
        res.json({ "success": true, "user": user, "token": token });

    } catch (error) {
        return res.json({"success": false, "message": error.message});
    }
};

export const loginUser = async (req, res) => {
    const { email, password } = req.body;
    try {
        const user = await User.findOne({ email });
        if (user) {
            const isMatch = await bcrypt.compare(password, user.password);
            if (isMatch) {
                const token = generateToken(user._id);
                return res.json({ "success": true, "user": user, "token": token });
            }
        } 
        return res.json({ "success": false, "message": "Invalid email or password" });
    } catch (error) {
        return res.json({ "success": false, "message": "Error logging in user" });
    }
};

export const getUser = async (req, res) => {
    try {
        const user = req.user;
        return res.json({ "success": true, "user": user });
    } catch (error) {
        return res.json({ "success": false, "message": error.message });
    }
};