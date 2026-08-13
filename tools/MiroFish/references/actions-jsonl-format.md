# actions.jsonl Format Reference

Each platform (`twitter/`, `reddit/`) has an `actions.jsonl` file — one JSON object per line.

## Event Types

Events are distinguished by the `event_type` field. Action events have NO `event_type` key.

### simulation_start (line 1)
```json
{
  "timestamp": "2026-...",
  "event_type": "simulation_start",
  "platform": "twitter",
  "total_rounds": 672,
  "agents_count": 13
}
```
Note: `total_rounds` is the theoretical max (rounds * agents), not the actual count.

### round_start / round_end
```json
{"timestamp": "...", "event_type": "round_start", "round": 10}
{"timestamp": "...", "event_type": "round_end", "round": 10}
```
One pair per round. These are bookkeeping events with no action content.

### simulation_end (last line)
```json
{"timestamp": "...", "event_type": "simulation_end", "platform": "twitter"}
```

### Action events (no `event_type` key)
Actions have these fields:
- `timestamp`: ISO datetime
- `round`: integer (which simulation round)
- `agent_name`: string (e.g. "Teenagers", "@TechFreedom", "MacroCorp")
- `action_type`: string — one of:
  - `CREATE_POST` — new post
  - `CREATE_COMMENT` — new comment (Reddit only)
  - `QUOTE_POST` — quote-repost with added commentary
  - `REPOST` — bare repost
  - `LIKE_POST` — like action
  - `DO_NOTHING` — agent chose to skip
- `action_args`: dict — varies by action type (see below)
- `success`: boolean

## action_args by Action Type

### CREATE_POST
```json
{"content": "post text here...", "post_id": 1}
```

### CREATE_COMMENT (Reddit)
```json
{"content": "comment text...", "comment_id": 1, "post_id": 1}
```

### QUOTE_POST
```json
{"quoted_id": 5, "new_post_id": 8, "original_content": "quoted text..."}
```

### REPOST
```json
{"new_post_id": 7, "original_content": "reposted text..."}
```

### LIKE_POST
```json
{"post_id": 5, "like_id": 1, "post_content": "liked post text..."}
```

### DO_NOTHING
```json
{}
```

## Parsing Tips

- **Discriminator**: action lines have NO `event_type` key. Bookkeeping events DO have it (`simulation_start`, `round_start`, `round_end`, `simulation_end`). Filter with:
  ```python
  actions = [e for e in events if 'event_type' not in e]
  ```
  Do NOT try to match `event_type == 'CREATE_POST'` etc. — the `event_type` key is simply absent from action lines.
- The `action_type` field (not `event_type`) holds the action kind: `CREATE_POST`, `REPOST`, `QUOTE_POST`, `LIKE_POST`, `CREATE_COMMENT`, `DO_NOTHING`.
- Content lives in `action_args.content` for posts/comments, `action_args.original_content` for reposts/quotes, and `action_args.post_content` for likes.
- A typical 20-round simulation on `parallel` platform yields ~30-35 action events (excluding bookkeeping) across both platforms. Twitter usually has more actions than Reddit.
- The `actions` API endpoint (`/api/simulation/<sim_id>/actions`) returns action types and agent names but content fields are often blank. For full content, parse the raw JSONL files or use the `/posts` and `/comments` endpoints.
- Content can be in any language (Chinese, English) depending on the simulation seed material.
- `agents_count` in `simulation_start` may differ from the actual number of agents that performed actions.
- Python parsing snippet:
  ```python
  import json
  with open('twitter/actions.jsonl') as f:
      events = [json.loads(line) for line in f if line.strip()]
  actions = [e for e in events if 'event_type' not in e]
  for a in actions:
      print(f"[Round {a['round']}] {a['agent_name']} — {a['action_type']}")
      args = a.get('action_args', {})
      content = args.get('content', args.get('original_content', args.get('post_content', '')))
      if content:
          print(f"  {content[:200]}")
  ```
