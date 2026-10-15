import { TICK_INTERVAL_MS } from '../config/constants';
import { GameSession } from './state';
import { CanvasRenderer } from '../render/canvas-renderer';
import { Overlay } from '../ui/overlay';
import { SoundEffects } from '../audio/sound-effects';

export class GameLoop {
  private lastTick = 0;
  private previousStatus = '';
  private previousScore = -1;
  constructor(private game: GameSession, private renderer: CanvasRenderer, private overlay: Overlay, private sound: SoundEffects) {}
  start(): void { requestAnimationFrame((time) => this.frame(time)); }
  private frame(time: number): void {
    if (this.game.status === 'RUNNING' && time - this.lastTick >= TICK_INTERVAL_MS) {
      this.lastTick = time;
      this.game.update();
      if (this.game.score > this.previousScore) this.sound.playEat();
    }
    if (this.game.status !== this.previousStatus || this.game.score !== this.previousScore) {
      this.overlay.update(this.game.status, this.game.score);
      if (this.game.status === 'GAME_OVER') this.sound.playGameOver();
      this.previousStatus = this.game.status;
      this.previousScore = this.game.score;
    }
    this.renderer.render(this.game);
    requestAnimationFrame((next) => this.frame(next));
  }
}
