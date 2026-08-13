---
name: MiroFish
description: Operate MiroFish swarm-intelligence prediction engine locally — prepare, launch, monitor, stop, and generate reports for multi-agent social simulations via its Flask REST API.
author: anonymized
date: 2026-08-13
version: 1.0
tags: [mirofish, swarm-intelligence, multi-agent, simulation, flask-api, python, uv]
---

# MiroFish Simulation Runner

## When to Use

- You need to launch, monitor, or stop a MiroFish multi-agent social simulation.
- You need to generate a prediction report from a completed simulation.
- You need to inspect simulation artefacts (actions, posts, timeline, agent stats).
- The user says "MiroFish", "swarm simulation", "agent prediction", or references a `sim_*` ID.

## Prerequisites

MiroFish requires:
- Python ≥3.11, ≤3.12 (NOT 3.13+ — the venv must be 3.12.x)
- `uv` package manager
- Node.js 18+ (for the frontend, not needed for API-only operation)
- A `.env` file with `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, and `ZEP_API_KEY`. MiroFish uses any OpenAI-compatible API endpoint; the default `.env` may point to a proxy (e.g. `api.example-proxy.com/v1`) wrapping a backend model (e.g. `example-model-name`). The `LLMClient` class reads `Config.LLM_BASE_URL` and `Config.LLM_MODEL_NAME` from `.env` with `override=True`, so whatever is in `.env` wins.
- A prepared simulation (profiles + config already generated)

## Project Layout

```
mirofish-project/
├── backend/
│   ├── app/
│   │   ├── api/            # Flask blueprints: simulation.py, report.py, graph.py
│   │   ├── services/       # simulation_manager.py, simulation_runner.py, report_agent.py, ...
│   │   └── utils/          # llm_client.py, zep.py, ...
│   ├── uploads/simulations/<sim_id>/
│   │   ├── simulation_config.json
│   │   ├── state.json
│   │   ├── twitter/actions.jsonl
│   │   ├── twitter_simulation.db
│   │   ├── reddit/actions.jsonl
│   │   ├── reddit_simulation.db
│   │   └── simulation.log
│   └── run.py             # Entry point
├── .env                   # LLM_API_KEY + ZEP_API_KEY
└── package.json
```

## Golden Rules

1. **Backend as process principal.** Start with `exec uv run python run.py` in the backend dir. Do NOT wrap in `nohup` or `&` — child processes get cleaned up by the orchestrator.
2. **Health-check before anything else.** `curl http://localhost:5001/health` must return 200 before calling any API.
3. **Always `force: true` when re-running.** If a simulation already has run artefacts, use `"force": true` on `/start` to clean old logs and restart fresh.
4. **Monitor both platforms.** The `parallel` mode runs Twitter and Reddit independently. Twitter often finishes later than Reddit. Check `twitter_completed` and `reddit_completed` separately.
5. **Call `/stop` after both platforms complete.** The runner status stays "running" even when both platforms show `completed=true`. You must POST to `/api/simulation/stop` to finalise and set `completed_at`.
6. **Report generation costs LLM quota.** The `/api/report/generate` endpoint makes LLM calls via the configured provider. Verify sufficient quota before launching — a failed report wastes the task slot. The error message may be in Chinese (e.g. `用户额度不足`) even if the provider is not a Chinese service — it can come from an upstream proxy.
7. **`generate/status` needs `task_id`, not `report_id`.** The status endpoint requires the `task_id` returned by `/generate`, not the `report_id`.

## Workflow

### Step 1 — Start the Backend

```bash
cd <mirofish-backend-dir>
exec uv run python run.py
```

Run as a background process (it's a Flask server). Verify after ~6-8 seconds:

```bash
curl -s http://localhost:5001/health --max-time 10
# Expect: {"service":"MiroFish Backend","status":"ok"}
```

### Step 2 — Verify Simulation Is Prepared

```bash
curl -s -X POST http://localhost:5001/api/simulation/prepare/status \
  -H "Content-Type: application/json" \
  -d '{"simulation_id": "sim_xxxx"}'
```

Look for `"status": "ready"` and `"prepare_info"` with `profiles_count` > 0.

### Step 3 — Launch the Simulation

```bash
curl -s -X POST http://localhost:5001/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_id": "sim_xxxx",
    "platform": "parallel",
    "max_rounds": 20,
    "force": true
  }'
```

Key parameters:
- `platform`: `"parallel"` (Twitter + Reddit), `"twitter"`, or `"reddit"`.
- `max_rounds`: Cap to control LLM cost. 20 rounds is a good default.
- `force`: `true` cleans old run logs/config (not profiles or simulation_config).

The response returns `process_pid`, `runner_status: "running"`, and per-platform flags.

### Step 4 — Monitor Progress

```bash
curl -s http://localhost:5001/api/simulation/sim_xxxx/run-status
```

Poll every 10-15 seconds. Watch:
- `runner_status` → should stay `"running"` until both platforms done.
- `twitter_completed` / `reddit_completed` → individual completion flags.
- `twitter_current_round` / `reddit_current_round` → progress per platform.
- `progress_percent` → overall (both platforms must reach 100%).

Reddit typically finishes first. Twitter takes longer per round.

### Step 5 — Stop the Simulation

Once both platforms show `completed=true`, call:

```bash
curl -s -X POST http://localhost:5001/api/simulation/stop \
  -H "Content-Type: application/json" \
  -d '{"simulation_id": "sim_xxxx"}'
```

This sets `runner_status: "stopped"` and `completed_at` timestamp.

### Step 6 — Inspect Results

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/simulation/<sim_id>/actions?limit=N` | GET | Action log (CREATE_POST, REPOST, LIKE_POST, QUOTE_POST...) |
| `/api/simulation/<sim_id>/posts?limit=N` | GET | Full post content with text |
| `/api/simulation/<sim_id>/timeline` | GET | Round-by-round timeline summary |
| `/api/simulation/<sim_id>/agent-stats` | GET | Per-agent action counts |
| `/api/simulation/<sim_id>/comments?limit=N` | GET | Comment content |

Note: The `actions` endpoint returns action types and agent names but content fields are often empty. Use the `posts` endpoint for actual text content. The raw JSONL files at `uploads/simulations/<sim_id>/twitter/actions.jsonl` and `reddit/actions.jsonl` contain everything.

### Step 7 — Generate Prediction Report

```bash
curl -s -X POST http://localhost:5001/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_id": "sim_xxxx",
    "prediction_requirements": "Summarize key opinions, sentiment trends, and conclusions..."
  }'
```

Capture `task_id` from the response. Then poll:

```bash
curl -s -X POST http://localhost:5001/api/report/generate/status \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<task_id>"}'
```

Status flows: `"generating"` → `"completed"` or `"failed"`.

Once completed, retrieve:

```bash
curl -s http://localhost:5001/api/report/<report_id>/download
curl -s http://localhost:5001/api/report/<report_id>/sections
```

### Step 8 — Deep Interaction (Optional)

```bash
# Chat with the report agent
curl -s -X POST http://localhost:5001/api/report/chat \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "report_xxxx",
    "message": "What was the dominant sentiment among teenagers?"
  }'

# Interview a specific agent
curl -s -X POST http://localhost:5001/api/simulation/interview \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_id": "sim_xxxx",
    "agent_name": "Teenagers",
    "question": "How do you feel about the regulation bill?"
  }'
```

## Pitfalls

### P1 — Backend dies silently after nohup
**Problem:** Starting the backend with `nohup … &` causes the orchestrator to clean up child processes when the wrapper terminates, killing the Flask server.
**Fix:** Use `exec uv run python run.py` as the process principal (no nohup, no &). The process replaces the shell.

### P2 — Runner stuck at "running" after both platforms complete
**Problem:** `runner_status` stays `"running"` even when `twitter_completed=true` and `reddit_completed=true`. There is no `completed_at` timestamp.
**Fix:** POST to `/api/simulation/stop` with the simulation_id. This finalises the run and sets the completed timestamp.

### P3 — Report generation fails with quota error
**Problem:** `/api/report/generate/status` returns `status: "failed"` with an error like `insufficient_user_quota` or `用户额度不足`.
**Fix:** The LLM provider (or its upstream proxy) is out of credit. Error messages may name a *different* provider than the one in `.env`. Example: `.env` points to `api.example-proxy.com/v1` (an OpenAI-compatible proxy), but the error mentions DashScope/Qwen because the proxy routes internally to an upstream provider. The proxy account and the upstream account can have independent quotas — the proxy forwards the upstream error verbatim. To diagnose, test the endpoint directly:
```bash
source .env
curl -s -X POST "${LLM_BASE_URL}/chat/completions" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"'"${LLM_MODEL_NAME}"'","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
```
Top up the proxy account or switch `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL_NAME` in `.env` to another OpenAI-compatible endpoint. Simulation data is NOT lost — you can regenerate the report later once quota is restored. **You MUST restart the backend** after editing `.env`: `load_dotenv(override=True)` runs once at import time in `config.py`, not per-request.

### P4 — generate/status endpoint rejects report_id
**Problem:** Calling `/api/report/generate/status` with `{"report_id": "..."}` returns `"请提供 task_id 或 simulation_id"`.
**Fix:** Use `"task_id"` (returned by `/generate`), not `"report_id"`. Alternatively, `"simulation_id"` also works.

### P5 — Actions API returns empty content
**Problem:** The `/api/simulation/<sim_id>/actions` endpoint returns action types and agent names but content fields are blank.
**Fix:** Use the `/posts` endpoint for text content, or read the raw JSONL files directly from `uploads/simulations/<sim_id>/{twitter,reddit}/actions.jsonl`.

### P6 — Python version mismatch
**Problem:** System Python is 3.13+ but MiroFish requires ≥3.11, ≤3.12.
**Fix:** The venv at `backend/.venv` was created with 3.12.x. Use `uv run` which automatically uses the project venv. Do NOT recreate it with system Python 3.13+.

## Typical Simulation Dynamics

Based on a completed 20-round parallel simulation (subject: social media regulation bill):

- **Rounds 1-9** — Agents have not yet interacted much. The first wave of actions typically starts around round 10 (after the simulation's internal warmup/graph-building phase).
- **Round 10** — Initial wave: 6-8 agents publish their opening posts (CREATE_POST). These set the narrative frames (e.g. privacy advocates frame the bill as surveillance; government frames it as child protection).
- **Round 11** — Amplification phase: agents who posted in round 10 get quoted, reposted, and liked. Agents who haven't yet acted join by commenting or reposting. Expect 8-12 action events on Twitter, 5-8 on Reddit.
- **Round 12** — Riposte phase: institutional actors (Government, Big Tech) respond with CREATE_POST. Other agents continue to like/repost.
- **Rounds 13-20** — Diminishing returns. Many actions are DO_NOTHING or repeated likes. New content drops sharply.
- **Twitter vs Reddit** — Twitter produces more volume (23 vs 11 actions) and more diverse action types (CREATE_POST, QUOTE_POST, REPOST, LIKE_POST). Reddit is more discussion-oriented (CREATE_POST + CREATE_COMMENT, fewer reposts).
- **Content language** — The seed material language determines agent output language. A Chinese seed produces Chinese-language posts even with an English-fluent model.
- **Most-replayed post** — Typically the one that frames the debate most emotionally (e.g. "privacy is the pillar of democracy"). It collects 5+ reposts/quotes/likes across rounds 11-12.
- **agent_count discrepancy** — `simulation_start` reports 13 agents but only 12 may appear in action stats. Not all agents act every round, and some may be passive by design.

## Verification

After completing a full run, verify:
1. `runner_status` is `"stopped"` (not `"running"`)
2. `completed_at` is set
3. `total_actions_count` > 0
4. Both `twitter_completed` and `reddit_completed` are `true`
5. `actions.jsonl` files exist and have line counts matching the action counts
6. (If report generated) `report_id` sections are retrievable

## API Reference

For the complete endpoint map (all 30+ routes across simulation, report, and graph blueprints), see `references/api-endpoint-map.md`.
For the `actions.jsonl` file format (event types, action_args schema, parsing tips), see `references/actions-jsonl-format.md`.

## Out of Scope

- Setting up a fresh MiroFish installation from scratch (see upstream README)
- Configuring Zep Cloud or LLM provider API keys (the `.env` supports any OpenAI-compatible endpoint via `LLM_BASE_URL` + `LLM_MODEL_NAME`)
- Building or modifying the frontend
- Custom entity/persona generation (covered by the `prepare` API flow)
- OASIS social media simulation internals (camel-ai library)
