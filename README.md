# DevCanvas 🎨

> **Autonomous AI Software Engineering Team — From Natural Language to Runnable Code**

DevCanvas is a multi-agent AI software engineering pipeline designed to transform natural-language software requirements into structured, runnable full-stack codebases.

It simulates a software development team consisting of a **Product Manager**, **Software Architect**, and **Developer**. The system combines LLM-based reasoning with deterministic validation to make AI-generated software development structured, auditable, and highly reliable.

---

## ✨ Key Features

### 🤖 Multi-Agent Software Engineering

DevCanvas separates software development into specialized, independent agents:

- **Product Manager:** Converts natural-language requirements into a structured Product Requirements Document (PRD).
- **Architect:** Translates the PRD into a system design, technology decisions, and file-level implementation plan.
- **Developer:** Generates the application code according to the approved architecture.

### 🔍 Deterministic Validation Pipeline

LLMs are non-deterministic and often hallucinate or write broken code. DevCanvas treats generated code as untrusted output and validates it independently of the model:

- **AST Parsing:** Validates Python syntax before execution.
- **Secret Scanning:** Prevents hardcoded API keys or credentials from being generated.
- **Placeholder Detection:** Catches lazy outputs (e.g., `# TODO: implement this`) and forces the agent to retry.
- **Structural Validation:** Ensures the generated file plans match the actual output.

### 🧠 Model-Agnostic LLM Layer

The system is designed to work with multiple LLM providers, allowing models to be selected based on cost, latency, or privacy.

- **Supported:** Groq (for high-speed inference), Google Gemini, and local **Ollama** models.
- Running local 7B models via Ollama allows for zero-cost cloud API usage while the validation pipeline ensures the generated code remains reliable.

### ⚡ Production-Grade Backend (FastAPI)

The backend is built with **FastAPI** and features:

- Asynchronous database operations via SQLAlchemy and PostgreSQL.
- JWT authentication with rotating refresh tokens and bcrypt password hashing.
- Strict resource-level authorization.
- Alembic for database migrations.

---

## 🏗️ System Architecture (Target Workflow)

The end goal is a deterministic state machine (via LangGraph) with Human-in-the-Loop (HITL) checkpoints to ensure maximum code reliability.

```mermaid
graph TD
    User([User Prompt]) --> PM[Product Manager Agent]

    PM -->|Generates PRD| Arch[Architect Agent]

    Arch -->|System Design + File Plan| Review1{Human Review}

    Review1 -->|Rejected| PM
    Review1 -->|Approved| Dev[Developer Agent]

    Dev -->|Generates Code| Valid[Deterministic Validation]

    Valid -->|AST Parsing / Secret Scan / Placeholder Detection| Review2{Human Code Review}

    Review2 -->|Rejected| Dev
    Review2 -->|Approved| Output([Runnable Codebase])
```

---

## 📁 Current Project Structure

```text
DevCanvas/
├── Agents/                  # Independent AI Agents (CLI execution)
│   ├── pm_agent.py          # Product Manager logic
│   ├── architect_agent.py   # System design logic
│   ├── developer_agent.py   # Code generation logic
│   ├── llm.py               # Model-agnostic LLM wrapper (Groq/Gemini/Ollama)
│   ├── output_store.py      # Manages agent outputs
│   └── test_*.py            # Agent testing scripts
│
├── backend/                 # FastAPI Application
│   ├── app/
│   │   ├── api/             # Route handlers
│   │   ├── models/          # SQLAlchemy DB models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── utils/           # Validation & helper scripts
│   │   ├── config.py        # Environment config
│   │   ├── db.py            # Database connection
│   │   └── main.py          # FastAPI entry point
│   ├── alembic/             # DB Migrations
│   └── alembic.ini
│
├── docker-compose.yml       # Container setup (PostgreSQL, etc.)
├── requirements.txt
└── README.md
```

---

## 🚦 Current Development Status

This project is actively being built in iterative phases to ensure production-grade reliability.

- [x] **Phase 1 (Complete):** Develop independent AI agents (PM, Architect, Developer) and the deterministic validation pipeline (AST, Secret Scanning). Test via CLI.
- [x] **Phase 2 (Complete):** Build the secure FastAPI backend foundation (Async PostgreSQL, JWT Auth, Alembic).
- [ ] **Phase 3 (In Progress):** Integrate the independent agents into a unified **LangGraph** state machine and expose them via FastAPI endpoints.
- [ ] **Phase 4 (Planned):** Build a React-based frontend for the Human-in-the-Loop (HITL) review checkpoints.

---

## 🛠️ Tech Stack

| Category | Technology |
| :--- | :--- |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy (Async) |
| Migrations | Alembic |
| AI Orchestration | LangChain *(LangGraph integration in progress)* |
| LLM Providers | Groq, Google Gemini, Ollama |
| Authentication | JWT, bcrypt |
| Validation | Python AST, Regex |
| Deployment | Docker |

---

## 💻 Getting Started

### 1. Clone the Repo & Setup

```bash
git clone https://github.com/your-username/devcanvas.git
cd devcanvas
python -m venv venv
```

Activate the virtual environment:

**macOS / Linux**

```bash
source venv/bin/activate
```

**Windows**

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in both the root and `backend/` directories:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/devcanvas
JWT_SECRET_KEY=your_secure_secret_key
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run the FastAPI Backend

```bash
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

Interactive API docs available at `http://localhost:8000/docs`.

### 4. Run the Agents (CLI)

Navigate to the `Agents` folder to test the independent agent workflows:

```bash
cd Agents
python pm_agent.py
```

---

## 🗺️ Roadmap

- [ ] Implement `graph.py` using LangGraph to connect agents.
- [ ] Bridge FastAPI endpoints to trigger the LangGraph workflow.
- [ ] React frontend for visual workflow management and HITL checkpoints.
- [ ] Playwright-based E2E testing of generated applications.
- [ ] Dockerize the entire pipeline for one-click deployment.

---

## 📜 License

This project is licensed under the MIT License.
