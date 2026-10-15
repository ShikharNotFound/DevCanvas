const express = require('express');
const bcrypt = require('bcryptjs');
const User = require('../models/User');
const auth = require('../utils/auth');

const router = express.Router();

router.post(['/','/register'], async (req, res, next) => {
  try {
    const name = String(req.body.name || '').trim();
    const email = String(req.body.email || '').trim().toLowerCase();
    const password = String(req.body.password || '');
    if (!name || !email || password.length < 8) {
      return res.status(400).json({ error: 'Name, email, and a password of at least 8 characters are required' });
    }
    const existing = await User.findOne({ email });
    if (existing) return res.status(409).json({ error: 'An account with this email already exists' });
    const user = await User.create({ name, email, password: await bcrypt.hash(password, 10) });
    return res.status(201).json({
      token: auth.generateToken(user),
      user: { id: user._id, name: user.name, email: user.email },
    });
  } catch (error) {
    if (error.code === 11000) return res.status(409).json({ error: 'An account with this email already exists' });
    return next(error);
  }
});

router.post('/login', async (req, res, next) => {
  try {
    const email = String(req.body.email || '').trim().toLowerCase();
    const password = String(req.body.password || '');
    const user = await User.findOne({ email }).select('+password');
    if (!user || !(await bcrypt.compare(password, user.password))) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }
    return res.json({
      token: auth.generateToken(user),
      user: { id: user._id, name: user.name, email: user.email },
    });
  } catch (error) {
    return next(error);
  }
});

module.exports = router;
