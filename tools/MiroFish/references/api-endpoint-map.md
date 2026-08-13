# MiroFish Backend API Endpoint Map

All endpoints are served by the Flask backend on port 5001.
Blueprints: `simulation_bp` (prefix `/api/simulation`), `report_bp` (prefix `/api/report`), `graph_bp`.

## Health

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |

## Simulation Control

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/simulation/create` | POST | Create a new simulation |
| `/api/simulation/prepare` | POST | Prepare simulation (generate entities, profiles, config) |
| `/api/simulation/prepare/status` | POST | Check if preparation is done |
| `/api/simulation/start` | POST | Launch the simulation (Twitter/Reddit/parallel) |
| `/api/simulation/stop` | POST | Stop a running simulation (finalise) |
| `/api/simulation/<sim_id>` | GET | Get simulation details |
| `/api/simulation/list` | GET | List all simulations |
| `/api/simulation/<sim_id>/run-status` | GET | Real-time run status (rounds, actions, completion) |
| `/api/simulation/<sim_id>/run-status/detail` | GET | Detailed run status |
| `/api/simulation/<sim_id>/config` | GET | Simulation config |
| `/api/simulation/<sim_id>/config/realtime` | GET | Realtime config |
| `/api/simulation/<sim_id>/config/download` | GET | Download config file |
| `/api/simulation/script/<script_name>/download` | GET | Download a script |
| `/api/simulation/generate-profiles` | POST | Generate agent profiles |
| `/api/simulation/env-status` | POST | Check environment status |
| `/api/simulation/close-env` | POST | Close environment |

## Simulation Data

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/simulation/history` | GET | Simulation history |
| `/api/simulation/<sim_id>/profiles` | GET | Agent profiles |
| `/api/simulation/<sim_id>/profiles/realtime` | GET | Realtime profiles |
| `/api/simulation/<sim_id>/actions` | GET | Action log (types + agents, content often empty) |
| `/api/simulation/<sim_id>/posts` | GET | Full posts with text content |
| `/api/simulation/<sim_id>/comments` | GET | Comments with text |
| `/api/simulation/<sim_id>/timeline` | GET | Round timeline summary |
| `/api/simulation/<sim_id>/agent-stats` | GET | Per-agent action statistics |

## Entity / Graph

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/simulation/entities/<graph_id>` | GET | List entities |
| `/api/simulation/entities/<graph_id>/<entity_uuid>` | GET | Get entity by UUID |
| `/api/simulation/entities/<graph_id>/by-type/<entity_type>` | GET | Filter entities by type |

## Agent Interview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/simulation/interview` | POST | Interview a single agent |
| `/api/simulation/interview/batch` | POST | Batch interview |
| `/api/simulation/interview/all` | POST | Interview all agents |
| `/api/simulation/interview/history` | POST | Interview history |

## Report

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/report/generate` | POST | Start report generation (async task) |
| `/api/report/generate/status` | POST | Poll generation status (use `task_id`, NOT `report_id`) |
| `/api/report/<report_id>` | GET | Get report details |
| `/api/report/by-simulation/<sim_id>` | GET | Find report by simulation |
| `/api/report/list` | GET | List all reports |
| `/api/report/<report_id>/download` | GET | Download report |
| `/api/report/<report_id>` | DELETE | Delete a report |
| `/api/report/chat` | POST | Chat with report agent |
| `/api/report/<report_id>/progress` | GET | Report generation progress |
| `/api/report/<report_id>/sections` | GET | Report sections |
| `/api/report/<report_id>/section/<index>` | GET | Specific report section |
| `/api/report/check/<sim_id>` | GET | Check if report exists for simulation |
| `/api/report/<report_id>/agent-log` | GET | Agent reasoning log |
| `/api/report/<report_id>/agent-log/stream` | GET | Stream agent reasoning log |
| `/api/report/<report_id>/console-log` | GET | Console log |
| `/api/report/<report_id>/console-log/stream` | GET | Stream console log |
| `/api/report/tools/search` | POST | Report tool: search |
| `/api/report/tools/statistics` | POST | Report tool: statistics |

## Key Parameter Reference

### `/start` body
```json
{
  "simulation_id": "sim_xxxx",
  "platform": "parallel|twitter|reddit",
  "max_rounds": 20,
  "enable_graph_memory_update": false,
  "force": false
}
```

### `/generate` body
```json
{
  "simulation_id": "sim_xxxx",
  "prediction_requirements": "Natural language description of what to predict/summarize"
}
```

### `/generate/status` body
```json
{
  "task_id": "uuid-from-generate-response"
}
```

## Raw Artefact Files

Located at `backend/uploads/simulations/<sim_id>/`:
- `simulation_config.json` — full config
- `state.json` — preparation state
- `env_status.json` — environment status
- `run_state.json` — run state (created after start)
- `simulation.log` — text log
- `twitter/actions.jsonl` — one JSON action per line
- `twitter_simulation.db` — SQLite DB for Twitter simulation
- `reddit/actions.jsonl` — one JSON action per line
- `reddit_simulation.db` — SQLite DB for Reddit simulation
- `twitter_profiles.csv` — agent profiles (CSV format)
- `reddit_profiles.json` — agent profiles (JSON format)
