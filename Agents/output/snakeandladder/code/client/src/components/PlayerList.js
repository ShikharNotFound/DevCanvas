import React from 'react';

export default function PlayerList({ players = [], positions = [] }) {
  return (
    <section>
      <h2>Players</h2>
      <ul className="players">
        {players.map((player) => {
          const position = positions.find((entry) => String(entry.player) === String(player._id));
          return <li key={player._id}>{player.name} <span>Square {position?.position ?? 0}</span></li>;
        })}
      </ul>
    </section>
  );
}
