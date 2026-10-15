import React, { useCallback, useEffect, useState } from 'react';
import { Link, useHistory, useParams } from 'react-router-dom';
import api from '../api';
import PlayerList from './PlayerList';

export default function GameSession() {
  const { code } = useParams();
  const history = useHistory();
  const [session, setSession] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const currentUser = JSON.parse(localStorage.getItem('user') || 'null');

  const loadSession = useCallback(async () => {
    try {
      const { data } = await api.get(`/sessions/${code}`);
      setSession(data.session);
      setError('');
    } catch (err) {
      setError(err.response?.data?.error || 'Could not load this game.');
    }
  }, [code]);

  useEffect(() => {
    loadSession();
    const timer = window.setInterval(loadSession, 3000);
    return () => window.clearInterval(timer);
  }, [loadSession]);

  async function action(name) {
    setBusy(true);
    setError('');
    try {
      const { data } = await api.post(`/sessions/${code}/${name}`);
      setSession(data.session);
      return true;
    } catch (err) {
      setError(err.response?.data?.error || 'That action failed.');
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function exitGame() {
    if (await action('exit')) history.push('/dashboard');
  }

  if (!localStorage.getItem('token')) return <main className="panel"><p><Link to="/">Sign in</Link> to play.</p></main>;
  if (!session) return <main className="panel"><p>{error || 'Loading game...'}</p><Link to="/dashboard">Back to lobby</Link></main>;

  const isHost = currentUser && session.host && String(session.host._id) === String(currentUser.id);
  const isTurn = currentUser && session.currentPlayer && String(session.currentPlayer._id) === String(currentUser.id);
  const positions = session.positions || [];

  return (
    <main className="game panel">
      <div className="topline">
        <div><h1>Room {session.code}</h1><p>Share this code with friends to invite them.</p></div>
        <button className="secondary" onClick={() => history.push('/dashboard')}>Lobby</button>
      </div>
      <PlayerList players={session.players} positions={positions} />
      <p className="status">
        {session.status === 'waiting' && 'Waiting for the host to start.'}
        {session.status === 'in-progress' && `Current turn: ${session.currentPlayer?.name || 'player'}`}
        {session.status === 'finished' && `Game over. Winner: ${session.winner?.name || 'no one'}`}
      </p>
      {session.lastRoll && <p>Last roll: {session.lastRoll}</p>}
      {session.status === 'waiting' && isHost && <button disabled={busy} onClick={() => action('start')}>Start game</button>}
      {session.status === 'in-progress' && isTurn && <button disabled={busy} onClick={() => action('roll')}>{busy ? 'Rolling...' : 'Roll the dice'}</button>}
      {session.status !== 'finished' && <button className="secondary" disabled={busy} onClick={exitGame}>Leave game</button>}
      <div className="board" aria-label="Game board">
        {Array.from({ length: 100 }, (_, index) => {
          const square = 100 - index;
          const occupants = positions.filter((entry) => entry.position === square);
          return <div className={occupants.length ? 'square occupied' : 'square'} key={square}>
            <span>{square}</span>{occupants.map((entry) => {
              const player = session.players.find((item) => String(item._id) === String(entry.player));
              return <b key={String(entry.player)} title={player?.name}>{player?.name?.slice(0, 1) || '*'}</b>;
            })}
          </div>;
        })}
      </div>
      {error && <p role="alert" className="error">{error}</p>}
    </main>
  );
}
