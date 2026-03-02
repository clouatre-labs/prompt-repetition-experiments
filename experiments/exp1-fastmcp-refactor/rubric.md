# Rubric: exp1-fastmcp-refactor

| Criterion | Description |
|---|---|
| C1 | Source file 1 identified: `src/math_mcp/tools/persistence.py` |
| C2 | Source file 2 identified: `src/math_mcp/tools/calculate.py` |
| C3 | Anti-pattern found: `id(ctx.lifespan_context)` |
| C4 | Replacement API correct: `ctx.set_state` / `ctx.get_state` with UUID |
| C5 | Must-Not constraint captured: non-serializable values, process-restart caveat |
| C6 | FastMCP docs consulted: `gofastmcp.com/servers/context` or equivalent |
