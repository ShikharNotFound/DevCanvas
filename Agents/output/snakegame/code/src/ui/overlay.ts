import type { GameStatus } from '../types';
import { GameSession } from '../engine/state';

export class Overlay {
  private root: HTMLDivElement;
  private heading: HTMLHeadingElement;
  private score: HTMLParagraphElement;
  private button: HTMLButtonElement;
  constructor(private game: GameSession, onStart: () => void) {
    this.root = document.createElement('div'); this.root.className = 'overlay';
    const content = document.createElement('div'); content.className = 'overlay-content';
    this.heading = document.createElement('h1'); this.score = document.createElement('p');
    this.button = document.createElement('button'); this.button.textContent = 'Start game';
    this.button.addEventListener('click', onStart);
    content.append(this.heading, this.score, this.button); this.root.append(content);
  }
  init(): void { document.body.append(this.root); this.update(this.game.status, this.game.score); }
  update(status: GameStatus, score: number): void {
    this.root.hidden = status === 'RUNNING';
    this.heading.textContent = status === 'GAME_OVER' ? 'Game over' : 'Snake';
    this.score.textContent = `Score: ${score}`;
    this.button.textContent = status === 'GAME_OVER' ? 'Play again' : 'Start game';
  }
}
