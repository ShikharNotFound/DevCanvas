# System Design Document

## 1. Overview
The Snake & Ladder Digital Game is a turn-based board game for 2-4 players. It uses a simple yet effective architecture to ensure quick, rule-accurate, and deterministic gameplay. The system consists of a frontend for user interaction, a backend for game logic and state management, and a database to store game sessions.

## 2. Technology Stack
| Category | Technology | Why |
|----------|------------|-----|
| Frontend | React.js | Modern, scalable, and widely-used for web applications. |
| Backend | Node.js with Express | Fast, scalable, and easy to set up for handling API requests. |
| Database | MongoDB | NoSQL database for storing game sessions and player data. |
| Auth | JWT | Secure and stateless authentication for user sessions. |
| Hosting | AWS EC2 | Scalable and reliable hosting for the backend services. |
| Hosting | AWS S3 | For storing static assets like images and styles. |
| Hosting | AWS RDS | For hosting the MongoDB database. |

## 3. File & Folder Structure
```
snake-ladder-game/
├── client/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── utils/
│   │   ├── App.js
│   │   ├── index.js
│   ├── package.json
├── server/
│   ├── controllers/
│   ├── models/
│   ├── routes/
│   ├── utils/
│   ├── app.js
│   ├── server.js
├── .env
├── package.json
```

## 4. Data Model
### User
- **name**: String (required)
- **email**: String (required)
- **password**: String (required, hashed)
- **sessions**: Array of ObjectIds (references to GameSession)

### GameSession
- **code**: String (required, unique)
- **host**: ObjectId (reference to User)
- **players**: Array of ObjectIds (references to User)
- **status**: String (e.g., "waiting", "in-progress", "finished")
- **board**: Array of Objects (positions of snakes and ladders)
- **currentPlayer**: ObjectId (reference to User)
- **winner**: ObjectId (reference to User, nullable)

## 5. API Endpoints
### User Endpoints
- **POST /api/v1/users**
  - **Purpose**: Register a new user.
  - **Request Body**: `{ name: String, email: String, password: String }`
  - **Response Body**: `{ token: String }`
  - **Status Codes**: 201 (Created), 400 (Bad Request), 409 (Conflict)
  - **Auth Required**: No

- **POST /api/v1/users/login**
  - **Purpose**: Authenticate a user.
  - **Request Body**: `{ email: String, password: String }`
  - **Response Body**: `{ token: String }`
  - **Status Codes**: 200 (OK), 401 (Unauthorized)
  - **Auth Required**: No

### GameSession Endpoints
- **POST /api/v1/sessions**
  - **Purpose**: Create a new game session.
  - **Request Body**: `{ code: String, host: ObjectId }`
  - **Response Body**: `{ session: GameSession }`
  - **Status Codes**: 201 (Created), 400 (Bad Request), 409 (Conflict)
  - **Auth Required**: Yes

- **GET /api/v1/sessions/:code**
  - **Purpose**: Get a game session by code.
  - **Response Body**: `{ session: GameSession }`
  - **Status Codes**: 200 (OK), 404 (Not Found)
  - **Auth Required**: Yes

- **POST /api/v1/sessions/:code/join**
  - **Purpose**: Join an existing game session.
  - **Request Body**: `{ player: ObjectId }`
  - **Response Body**: `{ session: GameSession }`
  - **Status Codes**: 200 (OK), 400 (Bad Request), 404 (Not Found)
  - **Auth Required**: Yes

- **POST /api/v1/sessions/:code/start**
  - **Purpose**: Start a game session.
  - **Response Body**: `{ session: GameSession }`
  - **Status Codes**: 200 (OK), 400 (Bad Request), 404 (Not Found)
  - **Auth Required**: Yes

- **POST /api/v1/sessions/:code/roll**
  - **Purpose**: Roll the dice and move the token.
  - **Response Body**: `{ session: GameSession }`
  - **Status Codes**: 200 (OK), 400 (Bad Request), 404 (Not Found)
  - **Auth Required**: Yes

- **POST /api/v1/sessions/:code/exit**
  - **Purpose**: Exit the game session.
  - **Response Body**: `{ session: GameSession }`
  - **Status Codes**: 200 (OK), 400 (Bad Request), 404 (Not Found)
  - **Auth Required**: Yes

## 6. Core User Flows
1. **User Registration**
   - Client → POST /api/v1/users
   - Server → Validates user data, hashes password, creates user, returns token

2. **Game Session Creation**
   - Client → POST /api/v1/sessions
   - Server → Validates session data, creates session, returns session details

3. **Player Joining**
   - Client → POST /api/v1/sessions/:code/join
   - Server → Validates player data, adds player to session, returns updated session details

4. **Game Start**
   - Client → POST /api/v1/sessions/:code/start
   - Server → Validates session state, starts game, returns updated session details

5. **Dice Roll and Token Movement**
   - Client → POST /api/v1/sessions/:code/roll
   - Server → Validates turn order, rolls dice, updates token position, returns updated session details

## 7. Authentication & Authorization
Users authenticate using JWT. The token is included in the Authorization header for all API requests. The server verifies the token on each request to ensure the user is authorized to perform the action.

## 8. External Dependencies
- **MongoDB**: For storing game sessions and player data.
- **AWS EC2**: For hosting the backend services.
- **AWS S3**: For storing static assets.
- **AWS RDS**: For hosting the MongoDB database.

## 9. Architectural Decisions
1. **Microservices Architecture**: The system is designed as a microservices architecture to allow for independent scaling and maintenance of different components.
2. **State Management**: The game state is managed in memory for quick access and updates. Optional persistence is provided using MongoDB.
3. **Cryptographically Secure PRNG**: The dice roll engine uses a cryptographically secure PRNG to ensure randomness.

## 10. Out of Scope
- Offline play
- AI opponent for single-player mode
- Customizable board layouts (user-defined snakes/ladders)
- Multiplayer over the internet with matchmaking service