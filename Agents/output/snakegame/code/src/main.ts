import './style.css';
import { GameSession } from './engine/state';
import { InputHandler } from './engine/input';
import { GameLoop } from './engine/loop';
import { CanvasRenderer } from './render/canvas-renderer';
import { SoundEffects } from './audio/sound-effects';
import { Overlay } from './ui/overlay';

const canvas = document.querySelector<HTMLCanvasElement>('#gameCanvas');
if (!canvas) throw new Error('Missing #gameCanvas element');

const game = new GameSession();
const renderer = new CanvasRenderer(canvas);
const sound = new SoundEffects();
const overlay = new Overlay(game, () => game.start());
const input = new InputHandler(game, sound);
const loop = new GameLoop(game, renderer, overlay, sound);

input.init();
overlay.init();
loop.start();
