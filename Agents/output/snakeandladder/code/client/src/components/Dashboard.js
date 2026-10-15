import React, { useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import api from '../api';

export default function Dashboard() {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const history = useHistory();

  async function createGame() {
    setBusy(true);
    setError('');
    try {
      const { data } = await api.post('/sessions');
      history.push(`/session/${data.session.code}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not create a game.');
      setBusy(false);
    }
  }

  async function joinGame(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const normalizedCode = code.trim().toUpperCase();
      await api.post(`/sessions/${normalizedCode}/join`);
      history.push(`/session/${normalizedCode}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not join this game.');
      setBusy(false);
    }
  }

  function signOut() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    history.replace('/');
  }

  if (!localStorage.getItem('token')) {
    return <main className="panel"><p>Please <Link to="/">sign in</Link> to play.</p></main>;
  }
  return (
    <main className="panel">
      <div className="topline"><h1>Snake &amp; Ladders</h1><button className="secondary" onClick={signOut}>Sign out</button></div>
      <p>Create a room and share its code, or join a friend's room.</p>
      <button disabled={busy} onClick={createGame}>{busy ? 'Please wait...' : 'Create a game'}</button>
      <form onSubmit={joinGame}>
        <label>Room code<input value={code} onChange={(e) => setCode(e.target.value)} required /></label>
        <button disabled={busy}>Join a game</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
    </main>
  );
}
