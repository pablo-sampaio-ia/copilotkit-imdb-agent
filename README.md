# IMDB Movies Analysis Agent

A LangGraph (Python) agent exposed over AG-UI, with a Next.js + CopilotKit
frontend, for exploring the IMDB top-movies-per-year dataset in natural
language. Ask for a chart, a written summary, or an ad-hoc analysis, and the
agent calls pandas-backed tools to answer from the real data.

## Features

- **Chat** — a CopilotKit sidebar chat interface.
- **Generative UI** — `plot_chart` results render as real, interactive
  bar/line/pie charts inline in the chat (`components/generative-ui/ChartRenderer.tsx`).
- **AG-UI Streams** — persistent Threads and the Inspector, via CopilotKit
  Intelligence.
- **Human-in-the-loop** — the agent asks for confirmation (`confirm_chart_spec`)
  before running a broad or ambiguous chart request.
- **Ad-hoc code analysis** — `run_python_analysis` runs a short, sandboxed
  Python snippet against the full dataframe for analysis the fixed tools
  don't cover.

## Project layout

- `agent/` — the Python LangGraph agent (FastAPI, port 8123). See `agent/main.py`
  and `agent/tools.py`.
- `app/`, `components/` — the Next.js frontend (port 3000).
- `data/world_imdb_movies_top_movies_per_year.csv` — the dataset both the
  agent and (optionally) any ad-hoc scripts read.

## Running it

```bash
# Terminal 1 — the Python agent
cd agent
uv run python main.py

# Terminal 2 — the frontend
npm install
npm run dev
```

Open http://localhost:3000. Set `OPENAI_API_KEY` in `agent/.env` (and
`CPK_INTELLIGENCE_API_KEY` in the root `.env`, written by `copilotkit onboard`)
before starting.
