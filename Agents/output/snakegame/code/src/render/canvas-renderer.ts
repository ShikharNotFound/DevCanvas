import { BACKGROUND_COLOR, CELL_SIZE, GRID_SIZE, FOOD_COLOR, SNAKE_COLOR } from '../config/constants';
import { GameSession } from '../engine/state';

export class CanvasRenderer {
  private context: CanvasRenderingContext2D;
  constructor(private canvas: HTMLCanvasElement) {
    canvas.width = GRID_SIZE * CELL_SIZE; canvas.height = GRID_SIZE * CELL_SIZE;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Canvas 2D context is unavailable');
    this.context = context;
  }
  render(game: GameSession): void {
    const ctx = this.context;
    ctx.fillStyle = BACKGROUND_COLOR; ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.fillStyle = FOOD_COLOR; ctx.fillRect(game.food.x * CELL_SIZE, game.food.y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    ctx.fillStyle = SNAKE_COLOR;
    for (const part of game.snake) ctx.fillRect(part.x * CELL_SIZE, part.y * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1);
  }
}
