# Development and install from source

Back to the [README](../README.md).

From source, for development ([uv](https://docs.astral.sh/uv/); Docker only for the server stack):

```bash
git clone https://github.com/octrow/buy-smarter && cd buy-smarter
uv sync
uv run buysmarter doctor      # tells you what is missing and what that turns off

# Optional pieces
uv sync --extra server && make up        # HTTP API stack: Postgres :5434 + Redis :6380 (see .env.example)
uv run playwright install chromium       # Ozon source
uv sync --extra style                    # clothing taste: an ONNX fashion model on the CPU
uv run buysmarter ozon-setup             # pass Ozon's anti-bot check once in a visible browser
cp .env.example .env                     # optional API keys and proxy
```

Price history, preferences and learned categories live in the **local store**, a SQLite file in the user
data dir (`~/.local/share/buysmarter/buysmarter.db` on Linux), created at first start. `doctor` shows where it
is. Every other piece is optional. The LLM comes from, in this order: an API key in the environment
(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`), a key you stored with
`buysmarter llm set-key <provider>` (kept in the OS keyring, never in a file), or the local `claude` CLI.
With none of them a run goes keyless (naive parser, no review summary) and the report says so;
`buysmarter llm status` shows which one is in use. In a clone, prefix the commands below with `uv run`.

## Development

```bash
make check   # ruff + pytest (no network or database server needed)
make test
make up / make down
```

Layout: `src/buysmarter/{normalize,db,llm,ranking,services,cli,knowledge,mcp_server,api}`, plus `jobs.py` (job
store in Redis), `worker.py` (taskiq worker) and `telemetry.py`; `deploy/` holds the Helm chart, the kind smoke test
and the observability configs. The marketplace
adapters live in a separate library, [market-sources](https://github.com/octrow/market-sources)
(`kaspi`/`olx`/`ozon` on top of a polite HTTP client and a Playwright session). Parser tests run on saved
JSON samples in `tests/samples/`. Notes from the source spikes are in [docs/spikes](spikes).
