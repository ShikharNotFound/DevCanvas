const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true
  },
  password: {
    type: String,
    required: true,
    select: false
  },
  sessions: [
    {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'GameSession'
    }
  ]
});

const User = mongoose.model('User', userSchema);

module.exports = User;
