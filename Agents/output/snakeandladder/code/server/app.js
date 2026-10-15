const express = require('express');
const cors = require('cors');
const userRoutes = require('./routes/userRoutes');
const gameSessionRoutes = require('./routes/gameSessionRoutes');

const app = express();
app.use(cors());
app.use(express.json());
app.get('/api/health', (req, res) => res.json({ status: 'ok' }));
app.use('/api/v1/users', userRoutes);
app.use('/api/v1/sessions', gameSessionRoutes);
app.use((req, res) => res.status(404).json({ error: 'Route not found' }));
app.use((err, req, res, next) => {
  console.error(err);
  res.status(err.status || 500).json({ error: err.message || 'Internal server error' });
});

module.exports = app;
