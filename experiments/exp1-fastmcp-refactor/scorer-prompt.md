# Scoring Delegate

Score all 10 Scout delegate outputs (control-1 through control-5, treatment-1 through treatment-5) against the rubric below.

## Scoring Rubric

Binary criteria, 0 or 1 each, max score 6 per run:

| # | Criterion | Expected value |
|---|---|---|
| C1 | Source file 1 identified | `src/math_mcp/tools/persistence.py` |
| C2 | Source file 2 identified | `src/math_mcp/tools/calculate.py` |
| C3 | Anti-pattern found | `id(ctx.lifespan_context)` |
| C4 | Replacement API correct | `ctx.set_state` / `ctx.get_state` with UUID |
| C5 | Must-Not constraint captured | non-serializable values, process-restart caveat |
| C6 | FastMCP docs consulted | `gofastmcp.com/servers/context` or equivalent |

## Task

1. Read all 10 Scout output files (scout-control-{1-5}.json, scout-treatment-{1-5}.json)
2. For each run, score against all 6 criteria (C1-C6)
3. Output a JSON file with per-run scores, justifications, and summary statistics
4. Compare control group (n=4, excluding control-1 which failed) vs treatment group (n=5)

## Output Format

```json
{
  "scored_at": "<ISO 8601 timestamp>",
  "scorer": "claude-haiku-4-5-blind",
  "rubric_version": "1.0",
  "note": "control-1 excluded from scoring (no output file produced; drift failure at 93 messages)",
  "scores": [
    {
      "run_id": "control-2",
      "C1": 1, "C2": 1, "C3": 1, "C4": 1, "C5": 1, "C6": 1,
      "total": 6,
      "justifications": {
        "C1": "...",
        "C2": "...",
        "C3": "...",
        "C4": "...",
        "C5": "...",
        "C6": "..."
      }
    }
  ]
}
```
