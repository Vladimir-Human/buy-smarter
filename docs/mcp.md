# MCP server

Back to the [README](../README.md).

buy-smarter is also an MCP server (fastmcp, stdio). The connected Claude acts as the conversational layer
and passes structured arguments (city, budget). The tools are thin wrappers over the same service and render
layers as the CLI.

```bash
uv run python -m buysmarter.mcp_server   # blocks on stdio; normally the client starts it
```

**Claude Code** picks up the `.mcp.json` in the repo root. For **Claude Desktop**, add to
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "buy-smarter": {
      "command": "uv",
      "args": ["run", "python", "-m", "buysmarter.mcp_server"],
      "cwd": "/path/to/buy-smarter"
    }
  }
}
```

| Tool | Purpose |
|---|---|
| `recommend` | Full pipeline → markdown report (best pick with axes, alternatives, top N, OLX used). Parameters: `query`, `city`, `budget`, `sources`, `trusted_only`, `top`, `parse_with_llm` (default `True`, as the CLI; without a configured LLM the run goes keyless and says so; `False` is faster), `answer`, `clarify_round`, `no_clarify`. An ambiguous request returns a question with options: ask the human and call again with `answer` and the `clarify_round` it names. |
| `search_products` | Raw search on one marketplace, no ranking (title, price, rating, url). |
| `compare` | 2–4 comma-separated products → side-by-side specs (Kaspi). |
| `get_preferences` / `set_preference` | Read/write preferences (city, budget…) in the local store. |
