---
name: MiroFish
description: "Multi-agent swarm intelligence engine for predicting outcomes via high-fidelity social simulation. Upload seed materials, generate agent personas, run parallel simulations, and produce prediction reports."
version: 1.0.0
author: DawnFolk
license: AGPL-3.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Simulation, MultiAgent, SwarmIntelligence, Prediction, LLM, GraphRAG, OASIS, Zep]
    related_skills: []
---

# MiroFish — Swarm Intelligence Prediction Engine

> A simple and universal swarm intelligence engine for predicting anything. Upload seed materials (news, reports, novels), and MiroFish constructs a parallel digital world where thousands of agents with personalities and memory interact, evolve, and reveal future trajectories.

GitHub: <https://github.com/666ghj/MiroFish>

---

## When to Use

- Predict public opinion trajectories from news or policy drafts
- Simulate social media reactions (Twitter, Reddit) to events
- Deduce fictional outcomes (e.g., "what happens next in this novel?")
- Rehearse decision-making in a zero-risk digital sandbox
- Test PR or policy scenarios before real-world deployment
- Explore multi-agent social emergence with GraphRAG-backed memory

## Prerequisites

- **Node.js** 18+ (`node -v`)
- **Python** ≥3.11, ≤3.12 (`python --version`)
- **uv** (Python package manager) — install via `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **LLM API key** — any OpenAI-compatible endpoint (e.g., Alibaba Qwen, OpenAI)
- **Zep Cloud API key** — free tier sufficient for simple usage (<https://app.getzep.com/>)

---

## Architecture Overview

```
MiroFish/
├── frontend/              Vue 3 + Vite SPA
│   └── src/
│       ├── views/         6 views (Home → Process → Simulation → Report → Interaction)
│       ├── components/    5 step components (Step1–Step5) + GraphPanel + HistoryDatabase
│       └── api/           Axios API clients (graph, simulation, report)
├── backend/               Flask 3 + Python
│   ├── app/
│   │   ├── api/           3 route modules: graph.py, simulation.py, report.py
│   │   ├── services/      12 service modules (graph_builder, simulation_runner, report_agent, zep_*, ontology_*, ...)
│   │   ├── models/        Project + Task models
│   │   ├── utils/         LLM client, file parser, Zep lifecycle/paging, OpenAI chat compat
│   │   └── config.py      Centralized Flask config loading from .env
│   ├── scripts/           IPC simulation runners (Twitter, Reddit, parallel)
│   └── tests/             16 test modules (Zep contracts, LLM JSON, ontology, platform profiles)
├── docker-compose.yml     Single-container deployment
├── Dockerfile             Python 3.11 + Node + uv
├── .env.example           Required env vars template
└── package.json           Root orchestrator (npm run setup:all / dev)
```

### Core Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, Vite, Vue Router, Pinia (store), Axios, i18n (en/zh) |
| Backend | Flask 3, Flask-CORS, Python 3.11–3.12 |
| LLM | OpenAI SDK (any compatible API), optional LLM Boost for acceleration |
| Memory | Zep Cloud (zep-cloud 3.25.0) — long-term agent memory + GraphRAG |
| Simulation Engine | CAMEL-AI OASIS (camel-oasis 0.2.5, camel-ai 0.2.78) |
| File Processing | PyMuPDF (PDF), charset-normalizer/chardet (encoding) |
| Validation | Pydantic 2 |

### 5-Phase Workflow

```
1. Graph Building   →  2. Environment Setup  →  3. Simulation  →  4. Report  →  5. Interaction
```

| Phase | What Happens | Key Service |
|---|---|---|
| **1. Graph Building** | Seed extraction from uploaded files (PDF/MD/TXT), GraphRAG construction, individual/collective memory injection into Zep | `graph_builder.py`, `zep_graph_memory_updater.py` |
| **2. Environment Setup** | Entity relationship extraction, persona generation, agent configuration injection | `ontology_generator.py`, `oasis_profile_generator.py`, `simulation_config_generator.py` |
| **3. Simulation** | Dual-platform (Twitter + Reddit) parallel simulation, dynamic temporal memory updates, auto-parse prediction requirements | `simulation_runner.py`, `simulation_ipc.py`, scripts `run_parallel_simulation.py` |
| **4. Report Generation** | ReportAgent uses rich toolset to analyze post-simulation state, produces prediction report | `report_agent.py` |
| **5. Deep Interaction** | Chat with any agent in the simulated world, interact with ReportAgent for follow-up questions | API `report.py`, frontend `InteractionView.vue` |

---

## Quick Start

### Option 1: Source Deployment (Recommended)

```bash
# 1. Clone
git clone https://github.com/666ghj/MiroFish.git
cd MiroFish

# 2. Configure environment
cp .env.example .env
# Edit .env — fill in LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME, ZEP_API_KEY

# 3. Install all dependencies (Node + Python)
npm run setup:all
#   → npm run setup      (root + frontend npm install)
#   → npm run setup:backend (cd backend && uv sync)

# 4. Start both frontend + backend
npm run dev
```

**Service URLs:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`

**Start services individually:**
```bash
npm run backend    # Backend only (cd backend && uv run python run.py)
npm run frontend   # Frontend only (cd frontend && npm run dev)
```

### Option 2: Docker Deployment

```bash
cp .env.example .env
docker compose up -d
```
Maps ports `3000 (frontend)` and `5001 (backend)`, reads `.env` from root, persists uploads to `./backend/uploads`.

### Environment Variables

```env
# LLM API (REQUIRED — any OpenAI-compatible endpoint)
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Zep Cloud (REQUIRED — free tier covers simple usage)
ZEP_API_KEY=your_zep_api_key

# Optional: LLM acceleration (omit these lines entirely if unused)
LLM_BOOST_API_KEY=your_boost_key
LLM_BOOST_BASE_URL=your_boost_url
LLM_BOOST_MODEL_NAME=your_boost_model
```

### Backend Configuration (`backend/app/config.py`)

Key configurable parameters (override via `.env`):

| Parameter | Default | Purpose |
|---|---|---|
| `FLASK_HOST` | `0.0.0.0` | Backend bind address |
| `FLASK_PORT` | `5001` | Backend port |
| `FLASK_DEBUG` | `False` | Flask debug mode (warn: not for production) |
| `MAX_CONTENT_LENGTH` | 50 MB | Max upload size |
| `ALLOWED_EXTENSIONS` | `pdf, md, txt, markdown` | Accepted seed file formats |
| `DEFAULT_CHUNK_SIZE` | 500 | Text chunking size for processing |
| `DEFAULT_CHUNK_OVERLAP` | 50 | Overlap between chunks |
| `OASIS_DEFAULT_MAX_ROUNDS` | `10` | Default simulation round count |
| `REPORT_AGENT_MAX_TOOL_CALLS` | `5` | Max tool calls per report generation |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | `2` | Max reflection iterations |
| `REPORT_AGENT_TEMPERATURE` | `0.5` | LLM temperature for report generation |

### Config Validation

The backend validates config on startup via `Config.validate()`:
- ✅ `LLM_API_KEY` must be set
- ✅ `ZEP_API_KEY` must be set
- ❌ `ZEP_API_URL` is NOT supported — MiroFish only connects to Zep Cloud
- ⚠️ `FLASK_DEBUG=True` triggers a RuntimeWarning (not for production)

If validation fails, the backend prints errors and exits with code 1.

---

## Complete Workflow Demonstration

### Phase 1 — Graph Building (Upload Seeds)

**Frontend (UI):** Navigate to Home → create new project → upload seed files (PDF/MD/TXT) → describe prediction requirements in natural language.

**Backend (API):**
```bash
# Upload seed file(s) + prediction request
POST /api/graph/build
Content-Type: multipart/form-data
  files: @report.pdf
  prediction_request: "What will public opinion look like after this policy?"
```

**What happens internally:**
1. `file_parser.py` extracts text from PDF (PyMuPDF) / MD / TXT, handles encoding via charset-normalizer
2. `text_processor.py` chunks text (`DEFAULT_CHUNK_SIZE=500`, overlap `50`)
3. `graph_builder.py` extracts entities and relationships via LLM
4. `ontology_generator.py` creates the ontology (entities, attributes, relations)
5. `zep_graph_memory_updater.py` injects individual + collective memory into **Zep Cloud** GraphRAG
6. Returns a `project_id` for use in subsequent phases

### Phase 2 — Environment Setup (Persona Generation)

**Frontend:** Navigate to `/process/:projectId` → Step 2 component (`Step2EnvSetup.vue`).

**Backend (API):**
```bash
# Generate personas and agent configurations
POST /api/simulation/setup
  project_id: <id>
  num_agents: 100  # optional, auto-derived from graph
```

**What happens internally:**
1. `ontology_generator.py` extracts entity relationships from the graph
2. `oasis_profile_generator.py` generates personas (personality, background, behavioral traits) via LLM
3. `simulation_config_generator.py` creates agent configurations for OASIS
4. Returns a `simulation_id` and config preview

### Phase 3 — Simulation (Dual-Platform Parallel)

**Frontend:** Navigate to `/simulation/:simulationId` → `SimulationRunView.vue` for live monitoring.

**Backend (API):**
```bash
# Start simulation
POST /api/simulation/start
  simulation_id: <id>
  max_rounds: 40   # keep <40 for first runs (cost!)
  platforms: ["twitter", "reddit"]
```

**What happens internally:**
1. `simulation_manager.py` orchestrates the run
2. `simulation_ipc.py` launches the IPC runner script in a subprocess
3. Script `run_parallel_simulation.py --config simulation_config.json` executes:
   - Dual-platform parallel simulation (Twitter + Reddit agents)
   - Each agent performs actions: `CREATE_POST`, `LIKE_POST`, `REPOST`, `FOLLOW`, `COMMENT`, `DISLIKE`, `QUOTE_POST`, `DO_NOTHING`, etc.
   - Dynamic temporal memory updates via `zep_graph_memory_updater.py`
   - Actions logged to `sim_xxx/twitter/actions.jsonl` and `sim_xxx/reddit/actions.jsonl`
4. Logs structured as:
   ```
   sim_xxx/
   ├── twitter/actions.jsonl
   ├── reddit/actions.jsonl
   ├── simulation.log
   └── run_state.json
   ```
5. After simulation completes, environment stays open for interview commands (unless `--no-wait`)

**Simulation runner scripts:**
```bash
# Twitter only
python run_twitter_simulation.py --config simulation_config.json

# Reddit only
python run_reddit_simulation.py --config simulation_config.json

# Dual platform (parallel)
python run_parallel_simulation.py --config simulation_config.json

# Run and close immediately (no interview mode)
python run_parallel_simulation.py --config simulation_config.json --no-wait

# Single platform flags
python run_parallel_simulation.py --config simulation_config.json --twitter-only
python run_parallel_simulation.py --config simulation_config.json --reddit-only
```

### Phase 4 — Report Generation

**Frontend:** Navigate to `/report/:reportId` → `ReportView.vue`.

**Backend (API):**
```bash
POST /api/report/generate
  simulation_id: <id>
  prediction_request: "Summarize the key opinion shifts observed"
```

**What happens internally:**
1. `report_agent.py` initializes ReportAgent with a tool-rich environment
2. Agent queries the post-simulation Zep graph for data
3. Agent makes up to `REPORT_AGENT_MAX_TOOL_CALLS=5` tool calls with `REPORT_AGENT_MAX_REFLECTION_ROUNDS=2` reflection iterations
4. LLM generates the report at `REPORT_AGENT_TEMPERATURE=0.5` (balanced creativity/accuracy)
5. Returns structured prediction report with evidence

### Phase 5 — Deep Interaction

**Frontend:** Navigate to `/interaction/:reportId` → `InteractionView.vue`.

**Backend (API):**
```bash
# Chat with any agent in the simulated world
POST /api/report/interact
  report_id: <id>
  agent_id: <agent_id from simulation>
  message: "Why did you repost that opinion?"
```

- Chat with any individual agent about their simulated behavior
- Interact with ReportAgent for follow-up analysis
- The simulated environment persists (IPC wait mode) for interactive querying

---

## Advanced Use Cases & Integrations

### LLM Provider Swapping
Any OpenAI-compatible API works — swap the `.env` variables:
```env
# OpenAI
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Alibaba Qwen (recommended by project, cheaper)
LLM_API_KEY=your_dashscope_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Local vLLM / Ollama
LLM_API_KEY=dummy
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL_NAME=your-model
```

### LLM Boost (Optional Acceleration)
A second, faster LLM handles lighter tasks (persona generation, config parsing) while the primary handles reasoning:
```env
LLM_BOOST_API_KEY=...
LLM_BOOST_BASE_URL=...
LLM_BOOST_MODEL_NAME=...
```
⚠️ If not using boost, **omit these lines entirely** from `.env` (presence triggers the codepath).

### OASIS Action Customization
Override the default available actions per platform in `.env` or `config.py`:
```python
OASIS_TWITTER_ACTIONS = ['CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST']
OASIS_REDDIT_ACTIONS = ['LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT', 'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER', 'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE']
```

### Docker Volume Persistence
Uploads persist to `./backend/uploads` (mapped in `docker-compose.yml`). Simulations create subdirectories under `uploads/simulations/`.

### Integration with CAMEL-AI / OASIS
MiroFish's simulation engine is built on [OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis) by CAMEL-AI. The `camel-oasis` package (v0.2.5) provides the social media simulation primitives.

---

## Golden Rules / Pitfalls

### Golden Rules
- **Start small** — first simulations should be **<40 rounds** to estimate API costs before scaling
- **Zep Cloud is mandatory** — there is no self-hosted Zep support (`ZEP_API_URL` is explicitly rejected by config validation)
- **Any OpenAI-compatible LLM works** — MiroFish is provider-agnostic via the OpenAI SDK format
- **Agent line + interview mode** — after simulation, the environment stays open (IPC) for agent interviews unless `--no-wait` is passed
- **Structured logs** — every simulation run produces `simulation.log`, `actions.jsonl`, and `run_state.json` for debugging and API queries
- **Config validation on startup** — `Config.validate()` exits with code 1 and prints clear errors if required keys are missing

### Pitfalls
- **Token consumption is HIGH** — hundreds of agents × multiple rounds = large API bills; always test with a small round count first
- **LLM Boost lines must be fully absent if unused** — leaving `LLM_BOOST_*` keys in `.env` with placeholder values triggers the boost codepath and will fail
- **Zep Cloud only** — `ZEP_API_URL` for self-hosted Zep is NOT supported (config validation rejects it)
- **Python version constraint** — `>= 3.11, < 3.13` — Python 3.13 is not supported (OASIS/CAMEL-AI dependency constraint)
- **Windows encoding monkey-patching** — the parallel simulation script monkey-patches `builtins.open` on Windows to force UTF-8; do not be alarmed if you see this
- **50MB upload limit** — `MAX_CONTENT_LENGTH` is hardcoded at 50MB; large PDFs may need chunking
- **Flask debug mode** — `FLASK_DEBUG=True` triggers a RuntimeWarning; never use in production
- **OASIS action set is finite** — agents can only perform the predefined actions listed in `config.py`; custom actions require modifying the constants

---

## Verification

### Verify services are running
```bash
# Check frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Expected: 200

# Check backend
curl -s http://localhost:5001/api/health 2>/dev/null || echo "No health endpoint — check port directly"
curl -s -o /dev/null -w "%{http_code}" http://localhost:5001
# Expected: 200 or 404 (Flask default for unknown routes)
```

### Verify configuration is valid
```bash
# Backend prints config errors on startup
cd backend && uv run python run.py
# If errors: prints "配置错误:" or "LLM_API_KEY 未配置" / "ZEP_API_KEY 未配置" and exits(1)
# If OK: Flask starts on 0.0.0.0:5001
```

### Verify simulation infrastructure
```bash
# Check simulation output structure after a run
find backend/uploads/simulations/ -type f -name "*.jsonl" -o -name "run_state.json" | sort

# Verify action logs have content
wc -l backend/uploads/simulations/sim_*/twitter/actions.jsonl
wc -l backend/uploads/simulations/sim_*/reddit/actions.jsonl

# Check simulation state
cat backend/uploads/simulations/sim_*/run_state.json | python -m json.tool
```

### Verify Zep Cloud connectivity
```bash
# Run the validation script
cd backend && uv run python scripts/validate_zep_cloud_integration.py
# Should output Zep session/user/graph creation success
```

### Verify tests pass
```bash
cd backend && uv run pytest -v
# 16 test modules covering: Zep contracts, paging, lifecycle, entity reader,
# graph memory, LLM JSON responses, ontology, platform profiles, simulation barriers
```

---

## Out of Scope

- Self-hosted Zep server support (`ZEP_API_URL` is rejected by design)
- Custom social media platforms beyond Twitter and Reddit (OASIS limitation)
- Real social media integration (simulations are synthetic sandbox environments)
- Training or fine-tuning LLM models (MiroFish uses inference-only)
- Production-grade authentication or multi-tenant isolation (single-user tool)
- Real-time streaming simulation output (logs are post-hoc structured files)
- Any prediction guarantee — MiroFish produces speculative simulations, not certified forecasts
