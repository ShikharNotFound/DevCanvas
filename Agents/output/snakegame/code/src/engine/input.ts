import type { Direction } from '../types';
import { GameSession } from './state';
import { SoundEffects } from '../audio/sound-effects';

const KEYS: Record<string, Direction> = {
  ArrowUp: 'UP', KeyW: 'UP', ArrowDown: 'DOWN', KeyS: 'DOWN',
  ArrowLeft: 'LEFT', KeyA: 'LEFT', ArrowRight: 'RIGHT', KeyD: 'RIGHT',
};

export class InputHandler {
  constructor(private game: GameSession, private sound: SoundEffects) {}
  init(): void {
    window.addEventListener('keydown', (event) => {
      const direction = KEYS[event.code];
      if (direction) { event.preventDefault(); this.game.setDirection(direction); }
      if (event.code === 'Space' && this.game.status !== 'RUNNING') {
        event.preventDefault(); this.sound.unlock(); this.game.start();
      }
    });
  }
}
