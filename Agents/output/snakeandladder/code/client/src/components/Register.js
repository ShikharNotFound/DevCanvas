import React, { useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import api from '../api';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const history = useHistory();

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const { data } = await api.post('/users/register', { name, email, password });
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      history.push('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Could not create your account. Try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="panel">
      <h1>Snake &amp; Ladders</h1>
      <h2>Create an account</h2>
      <form onSubmit={handleSubmit}>
        <label>Name<input value={name} onChange={(e) => setName(e.target.value)} required /></label>
        <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
        <label>Password<input type="password" minLength="8" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
        {error && <p role="alert" className="error">{error}</p>}
        <button disabled={busy}>{busy ? 'Creating account...' : 'Register'}</button>
      </form>
      <p>Already have an account? <Link to="/">Sign in</Link></p>
    </main>
  );
}
