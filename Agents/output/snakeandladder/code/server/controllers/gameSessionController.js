const express = require('express');
const crypto = require('crypto');
const GameSession = require('../models/GameSession');
const auth = require('../utils/auth');

const router = express.Router();
const jumps = { 4: 14, 9: 31, 20: 38, 28: 84, 40: 59, 51: 67, 63: 81, 71: 91,
  17: 7, 54: 34, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 99: 78 };
const isSameId = (a, b) => a && b && a.toString() === b.toString();
const findSession = (code) => GameSession.findOne({ code: String(code).toUpperCase() });
const sendSession = async (res, session, status) => {
  await session.populate('players host currentPlayer winner').execPopulate();
  return res.status(status || 200).json({ session });
};

router.use(auth);

router.post('/', async (req, res, next) => {
  try {
    const code = crypto.randomBytes(3).toString('hex').toUpperCase();
    const session = await GameSession.create({
      code, host: req.user._id, players: [req.user._id],
      positions: [{ player: req.user._id, position: 0 }],
    });
    return sendSession(res, session, 201);
  } catch (error) { return next(error); }
});

router.get('/:code', async (req, res, next) => {
  try {
    const session = await findSession(req.params.code);
    if (!session) return res.status(404).json({ error: 'Game session not found' });
    if (!session.players.some((player) => isSameId(player, req.user._id))) {
      return res.status(403).json({ error: 'Join this session to view it' });
    }
    return sendSession(res, session);
  } catch (error) { return next(error); }
});

router.post('/:code/join', async (req, res, next) => {
  try {
    const session = await findSession(req.params.code);
    if (!session) return res.status(404).json({ error: 'Game session not found' });
    if (session.status !== 'waiting') return res.status(400).json({ error: 'This game has already started' });
    if (!session.players.some((player) => isSameId(player, req.user._id))) {
      session.players.push(req.user._id);
      session.positions.push({ player: req.user._id, position: 0 });
      await session.save();
    }
    return sendSession(res, session);
  } catch (error) { return next(error); }
});

router.post('/:code/start', async (req, res, next) => {
  try {
    const session = await findSession(req.params.code);
    if (!session) return res.status(404).json({ error: 'Game session not found' });
    if (!isSameId(session.host, req.user._id)) return res.status(403).json({ error: 'Only the host can start the game' });
    if (session.status !== 'waiting') return res.status(400).json({ error: 'Game session is not waiting' });
    session.status = 'in-progress';
    session.currentPlayer = session.host;
    await session.save();
    return sendSession(res, session);
  } catch (error) { return next(error); }
});

router.post('/:code/roll', async (req, res, next) => {
  try {
    const session = await findSession(req.params.code);
    if (!session) return res.status(404).json({ error: 'Game session not found' });
    if (session.status !== 'in-progress') return res.status(400).json({ error: 'Game session is not in progress' });
    if (!isSameId(session.currentPlayer, req.user._id)) return res.status(400).json({ error: 'It is not your turn' });

    const roll = crypto.randomInt(1, 7);
    const playerPosition = session.positions.find((entry) => isSameId(entry.player, req.user._id));
    const landed = playerPosition.position + roll;
    if (landed <= 100) playerPosition.position = jumps[landed] || landed;
    session.lastRoll = roll;
    if (playerPosition.position === 100) {
      session.status = 'finished';
      session.winner = req.user._id;
    } else {
      const currentIndex = session.players.findIndex((player) => isSameId(player, req.user._id));
      session.currentPlayer = session.players[(currentIndex + 1) % session.players.length];
    }
    await session.save();
    return sendSession(res, session);
  } catch (error) { return next(error); }
});

router.post('/:code/exit', async (req, res, next) => {
  try {
    const session = await findSession(req.params.code);
    if (!session) return res.status(404).json({ error: 'Game session not found' });
    const index = session.players.findIndex((player) => isSameId(player, req.user._id));
    if (index < 0) return res.status(400).json({ error: 'You are not in this session' });
    session.players.splice(index, 1);
    session.positions = session.positions.filter((entry) => !isSameId(entry.player, req.user._id));
    if (isSameId(session.currentPlayer, req.user._id)) {
      session.currentPlayer = session.players.length ? session.players[index % session.players.length] : null;
    }
    if (isSameId(session.host, req.user._id) && session.players.length) session.host = session.players[0];
    if (!session.players.length && session.status !== 'finished') session.status = 'finished';
    await session.save();
    return sendSession(res, session);
  } catch (error) { return next(error); }
});

module.exports = router;
