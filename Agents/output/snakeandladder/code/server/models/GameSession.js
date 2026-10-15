const mongoose = require('mongoose');

const gameSessionSchema = new mongoose.Schema({
  code: {
    type: String,
    required: true,
    unique: true
  },
  host: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  players: [
    {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true
    }
  ],
  status: {
    type: String,
    enum: ['waiting', 'in-progress', 'finished'],
    default: 'waiting'
  },
  board: [
    {
      type: Object
    }
  ],
  positions: [{
    _id: false,
    player: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    position: { type: Number, default: 0, min: 0, max: 100 }
  }],
  lastRoll: { type: Number, min: 1, max: 6 },
  currentPlayer: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  winner: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('GameSession', gameSessionSchema);
