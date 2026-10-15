import type { Coordinate, Direction, GameStatus } from '../types';
import { DIRECTIONS } from '../types';
import { GRID_SIZE, SNAKE_START_POSITION } from '../config/constants';

export class GameSession {
  status: GameStatus = 'IDLE';
  score = 0;
  snake: Coordinate[] = [{ ...SNAKE_START_POSITION }];
  direction: Direction = 'RIGHT';
  pendingDirection: Direction = 'RIGHT';
  food: Coordinate = this.randomFood();

  start(): void { if (this.status === 'GAME_OVER') this.reset(); this.status = 'RUNNING'; }
  reset(): void {
    this.status = 'IDLE'; this.score = 0; this.snake = [{ ...SNAKE_START_POSITION }];
    this.direction = 'RIGHT'; this.pendingDirection = 'RIGHT'; this.food = this.randomFood();
  }
  setDirection(direction: Direction): void {
    const current = DIRECTIONS[this.direction]; const next = DIRECTIONS[direction];
    if (current.x + next.x !== 0 || current.y + next.y !== 0) this.pendingDirection = direction;
  }
  update(): void {
    if (this.status !== 'RUNNING') return;
    this.direction = this.pendingDirection;
    const vector = DIRECTIONS[this.direction]; const head = this.snake[0];
    const next = { x: head.x + vector.x, y: head.y + vector.y };
    const eating = next.x === this.food.x && next.y === this.food.y;
    const body = eating ? this.snake : this.snake.slice(0, -1);
    if (next.x < 0 || next.x >= GRID_SIZE || next.y < 0 || next.y >= GRID_SIZE || body.some((p) => p.x === next.x && p.y === next.y)) {
      this.status = 'GAME_OVER'; return;
    }
    this.snake.unshift(next);
    if (eating) { this.score += 1; this.food = this.randomFood(); } else this.snake.pop();
  }
  private randomFood(): Coordinate {
    const free: Coordinate[] = [];
    for (let y = 0; y < GRID_SIZE; y += 1) for (let x = 0; x < GRID_SIZE; x += 1) {
      if (!this.snake?.some((part) => part.x === x && part.y === y)) free.push({ x, y });
    }
    return free.length ? free[Math.floor(Math.random() * free.length)] : { x: 0, y: 0 };
  }
}
