import React from 'react';

export default function DiceRoll({ onRoll, disabled = false }) {
  return <button type="button" disabled={disabled} onClick={onRoll}>Roll the dice</button>;
}
