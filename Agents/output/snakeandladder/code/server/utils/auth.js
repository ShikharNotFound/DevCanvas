const jwt = require('jsonwebtoken');
const User = require('../models/User');

const secret = () => {
  if (!process.env.JWT_SECRET) throw new Error('JWT_SECRET is not configured');
  return process.env.JWT_SECRET;
};

function generateToken(user) {
  return jwt.sign({ userId: user._id.toString() }, secret(), { expiresIn: '7d' });
}

async function auth(req, res, next) {
  const header = req.get('authorization') || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: 'Authentication required' });

  try {
    const payload = jwt.verify(token, secret());
    const user = await User.findById(payload.userId).select('-password');
    if (!user) return res.status(401).json({ error: 'Account not found' });
    req.user = user;
    return next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

auth.generateToken = generateToken;
module.exports = auth;
