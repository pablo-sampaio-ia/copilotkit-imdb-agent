"""FastAPI + LangGraph agent for the IMDB movies-analysis project.

Serves a LangGraph agent over AG-UI on port 8123, for the Next.js CopilotKit
runtime at ``app/api/copilotkit/[[...slug]]/route.ts`` to connect to via
``HttpAgent``. The agent answers questions about the IMDB top-movies-per-year
dataset by calling pandas-backed tools in ``tools.py``: two fixed,
parameterized tools (`plot_chart`, `analyze_data`) for charts and summaries,
plus a restricted `run_python_analysis` sandbox for ad-hoc analysis beyond
what those two cover.
"""

import os

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import CopilotKitMiddleware, CopilotKitState, LangGraphAGUIAgent
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
import uvicorn

from tools import analyze_data, list_columns, plot_chart, run_python_analysis

load_dotenv()

MODEL = os.getenv("COPILOTKIT_AGENT_MODEL", "openai:gpt-5.6-luna")

SYSTEM_PROMPT = """
You are the IMDB Movies assistant. You help users explore a dataset of the \
top-rated movies per year worldwide, with fields like title, year, rating, \
vote count, budget, box-office gross, director, cast, genre, country, and \
awards (wins/nominations/Oscars).

You have these tools:
- list_columns: look up the available fields and their friendly aliases
  (e.g. "rating", "votes", "revenue", "country").
- plot_chart: compute an aggregation with pandas and return structured chart
  JSON (bar, line, or pie). This is the ONLY way you show a chart -- never
  describe a chart in prose instead of calling this tool, and never claim to
  have produced an image.
- analyze_data: compute a short statistical summary (count/total/mean/min/max)
  grouped by a field, for a written analysis.
- run_python_analysis: run a short Python snippet against the full dataframe
  (available as `df`) for analysis plot_chart/analyze_data don't cover --
  correlations, custom multi-column groupings, inspecting messy fields like
  "genre", top-N by more than one criterion, etc. It is sandboxed (no file,
  network, or import access) and times out after 10 seconds. It returns text,
  never a chart -- use plot_chart for anything the user should see rendered.
- confirm_chart_spec (frontend tool): shows the user your proposed chart type,
  fields, and filters and lets them approve or edit it before you call
  plot_chart.

Quality gate -- call confirm_chart_spec BEFORE calling plot_chart whenever the
request is broad or ambiguous: no specific column(s) named, no filters at
all, or a request spanning the whole dataset / "everything" / "all movies".
Skip the confirmation only when the user's request already names specific
fields, filters, or a narrow scope (e.g. one genre, one decade).

Always ground your answers in tool results. If a tool call returns an error
or empty result, tell the user what was missing instead of guessing. Keep
prose replies brief and use Markdown tables for any numeric summaries you
write by hand.
"""

graph = create_agent(
    model=MODEL,
    tools=[list_columns, plot_chart, analyze_data, run_python_analysis],
    middleware=[CopilotKitMiddleware()],
    system_prompt=SYSTEM_PROMPT,
    state_schema=CopilotKitState,
    checkpointer=MemorySaver(),
)

app = FastAPI()

add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="imdb_agent",
        description=(
            "Analyzes the IMDB top-movies-per-year dataset and renders "
            "charts and summaries from it."
        ),
        graph=graph,
    ),
    path="/",
)


def main():
    """Run the uvicorn server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8123,
        reload=True,
    )


if __name__ == "__main__":
    main()
