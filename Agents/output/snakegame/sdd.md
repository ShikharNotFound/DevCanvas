# System Design Document

## 1. Overview
The application is a lightweight, zero-dependency browser-based recreation of the classic Snake game delivered as a static single-page application (SPA). The architecture employs a client-side Model-View-Controller (MVC) pattern utilizing an HTML5 Canvas renderer driven by a decoupled fixed-timestep game loop. Primary client components include the Game State Engine, Input Controller, Canvas Renderer, and Web Audio Sound Generator.

## 2. Technology Stack

| Category | Technology | Why |
| :--- | :--- | :--- |
| Frontend Language | TypeScript | Static typing guarantees deterministic coordinate math and eliminates runtime state bugs. |
| Rendering Engine | HTML5 Canvas 2D API | High-throughput rendering capable of maintaining 60 fps without DOM tree reflow overhead. |
| Audio Engine | Web Audio API | Generates synthetic sound waves procedurally, eliminating external audio assets and network requests. |
| Build Tool | Vite | Produces an optimized, tree-shaken static bundle under 30 KB to satisfy the 2-second 3G load requirement. |
| Testing | Vitest | Fast execution of headless unit tests for grid collision detection, movement logic, and spawning algorithms. |
| Hosting & CDN | Cloudflare Pages | Global edge-cached static file delivery providing zero cold starts, automated HTTPS, and sub-second TTFB. |

## 3. File & Folder Structure

```text
snake-game/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── public/
│   ├── favicon.ico
│   └── robots.txt
└── src/
    ├── main.ts
    ├── style.css
    ├── config/
    │   └── constants.ts
    ├── audio/
    │   └── sound-effects.ts
    ├── engine/
    │   ├── loop.ts
    │   ├── input.ts
    │   └── state.ts
    ├── entities/
    │   ├── snake.ts
    │   └── food.ts
    ├── render/
    │   └── canvas-renderer.ts
    ├── types/
    │   └── index.ts
    └── ui/
        └── overlay.ts
```

## 4. Data Model

The application operates entirely client-side using in-memory state models. No database is required.

### Coordinate
Represents a discrete grid position.
- `x`: `number` (Integer, 0 to 19; column position on grid)
- `y`: `number` (Integer, 0 to 19; row position on grid)

### Snake
Represents the player-controlled entity.
- `body`: `Coordinate[]` (Array of segments where index 0 is the head and the last element is the tail)
- `direction`: `Direction` (`"UP" | "DOWN" | "LEFT" | "RIGHT"`; current vector of travel)
- `pendingDirection`: `Direction` (`"UP" | "DOWN" | "LEFT" | "RIGHT"`; next validated turn queued for processing)

### Food
Represents consumable items on the grid.
- `position`: `Coordinate` (Grid location of the active food pellet)

### GameSession
Represents runtime game lifecycle and score state.
- `status`: `GameStatus` (`"IDLE" | "RUNNING" | "GAME_OVER"`)
- `score`: `number` (Current score; starts at 0, increments by 1 per food pellet consumed)
- `tickIntervalMs`: `number` (Game logic advancement speed, set to 100 ms)
- `gridSize`: `number` (Dimensions of the square grid, set to 20)
- `isMuted`: `boolean` (Audio toggle state)

Relationships:
- A `GameSession` owns exactly one `Snake` instance and one `Food` instance at any time during gameplay.
- Each `Snake` is composed of 1 or more `Coordinate` segments.
- Each `Food` holds exactly one `Coordinate`.

## 5. API Endpoints

This is an exclusively client-side web application deployed as pre-compiled static files. There are no backend REST or GraphQL endpoints.

All operational assets are served via static web hosting:
- `GET /`
  - Purpose: Delivers static HTML shell.
  - Request body: None
  - Response body: `index.html`
  - Status codes: `200`, `304`
  - Auth required: No

- `GET /assets/[name]-[hash].js`
  - Purpose: Delivers application bundle.
  - Request body: None
  - Response body: Minified JavaScript runtime
  - Status codes: `200`, `304`
  - Auth required: No

## 6. Core User Flows

### Flow 1: Game Start and Loop Initialization
1. Client loads `index.html`, which triggers `main.ts` to instantiate `GameSession`, `CanvasRenderer`, `InputHandler`, and `SoundEffects`.
2. UI displays the start screen overlay with a "Play" button.
3. User clicks "Play" or presses the Space/Enter key.
4. Input listener notifies `GameSession` to transition `status` from `IDLE` to `RUNNING`.
5. `GameSession` sets the snake centered at grid coordinates `(10, 10)` moving `RIGHT`, and calculates a random valid coordinate for the first `Food`.
6. `Loop` begins firing:
   - Fixed-step timer processes game logic every 100 ms.
   - `requestAnimationFrame` continuously calls `CanvasRenderer` to clear and redraw canvas at native display refresh rate (60 fps).

### Flow 2: Frame Update, Input Processing, and Pellet Consumption
1. User presses an arrow key (e.g., `ArrowDown`).
2. `InputHandler` captures the `keydown` event, verifies the direction is not 180° opposite of `Snake.direction`, and assigns it to `Snake.pendingDirection`.
3. Fixed-timestep tick executes:
   - `Snake.direction` updates to `Snake.pendingDirection`.
   - New head position is calculated by adding direction vector to head coordinate.
   - Collision check against current `Food.position`:
     - If true: New head is prepended to `Snake.body`, tail segment is retained (snake grows), `GameSession.score` increments by 1, `SoundEffects.playEat()` triggers oscillator tone, and `Food.position` recalculates on an unoccupied cell.
     - If false: New head is prepended to `Snake.body`, and the last segment is popped from the array.
4. Canvas renders the updated positions.

### Flow 3: Collision Detection and Game Over Reset
1. Fixed-timestep tick calculates the proposed head position.
2. System evaluates bounds:
   - Wall check: `x < 0` OR `x >= gridSize` OR `y < 0` OR `y >= gridSize`.
   - Self-collision check: Proposed head matches any coordinate in `Snake.body[1..n]`.
3. If either condition evaluates to true:
   - `GameSession.status` transitions immediately to `GAME_OVER`.
   - Loop pauses updates.
   - `SoundEffects.playGameOver()` triggers low-frequency tone.
   - `Overlay` renders the game-over dialog displaying the final score and a "Restart" button.
4. User clicks "Restart":
   - `GameSession` state resets to initial values.
   - Flow returns to step 4 of Flow 1.

## 7. Authentication & Authorization
No authentication or authorization mechanisms are implemented. The application is an unauthenticated, zero-friction client-side utility designed for immediate play without accounts, sessions, tokens, or profile storage.

## 8. External Dependencies
- **None (Zero external runtime libraries):** All graphics are rendered using the standard browser `CanvasRenderingContext2D`. All sound is generated using the browser's built-in `AudioContext` and `OscillatorNode`. This eliminates third-party downtime, avoids external tracking, enforces a strict zero-trust Content Security Policy, and guarantees minimum payload size.

## 9. Architectural Decisions

- **Canvas 2D Rendering over DOM Grid Nodes:**
  *Decision:* Use a single HTML5 `<canvas>` element rather than a grid of 400 `<div>` elements.
  *Justification:* Manipulating 400 DOM elements causes layout reflows and garbage collection pauses, risking frame drops below the target 60 fps threshold. Canvas offers direct rasterization with predictable CPU utilization under 5%.

- **Synthesized Audio over Audio Asset Files:**
  *Decision:* Use Web Audio API oscillators for sound effects instead of `.mp3` or `.wav` files.
  *Justification:* Procedural tones require zero bytes of network bandwidth, eliminate asset preloading delays, and avoid browser media playback buffering issues.

- **Fixed Timestep Logic Decoupled from Render Refresh:**
  *Decision:* Run game logic at a fixed rate (10 ticks per second) inside `requestAnimationFrame` with accumulated delta time, rather than relying on `setInterval`.
  *Justification:* `setInterval` drifts over time and throttles inconsistently in inactive tabs. Decoupled delta loops ensure deterministic snake speed across different monitor refresh rates (60 Hz, 120 Hz, 144 Hz).

- **Input Buffering via Pending Direction:**
  *Decision:* Buffer only a single next direction input per tick.
  *Justification:* Prevents a common Snake failure mode where a user rapidly presses two arrow keys (e.g., `Down` then `Left` while moving `Right`) within a single frame, triggering an unintentional self-collision before the first turn completes.

## 10. Out of Scope
- Backend database, server APIs, and persistent global leaderboards.
- User accounts, authentication, and cloud-synced progress.
- Touch gesture controls and on-screen virtual d-pad (focused strictly on desktop keyboard input).
- Multiplayer, turn-based, or network play.
- Local persistence (saving high scores to browser `localStorage` is deferred to future iterations).
- Custom skinning, sprite packs, and complex visual shaders.