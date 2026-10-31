"""Servidor do agente: FastAPI + LangGraph exposto por AG-UI na porta 8123.

O runtime do Next.js (app/api/copilotkit/[[...slug]]/route.ts) conecta aqui
com um `HttpAgent`. A lógica de dados está no pacote `imdb/`:

    imdb/data.py            carga do CSV, colunas e apelidos
    imdb/filters.py         filtros em JSON
    imdb/charts.py          especificações de gráfico
    imdb/summary.py         resumos em texto
    imdb/python_sandbox.py  trechos de Python (e figuras)
    imdb/tools.py           as ferramentas que o agente enxerga
    imdb/prompt.py          o system prompt
"""

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import CopilotKitMiddleware, CopilotKitState, LangGraphAGUIAgent
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
import uvicorn

from imdb.config import MODEL, check_environment
from imdb.images import image_path
from imdb.prompt import SYSTEM_PROMPT
from imdb.tools import ALL_TOOLS

check_environment()

# `create_agent` monta um grafo ReAct (modelo <-> ferramentas). O
# CopilotKitMiddleware injeta as ferramentas e o contexto vindos do front-end.
graph = create_agent(
    model=MODEL,
    tools=ALL_TOOLS,
    middleware=[CopilotKitMiddleware()],
    system_prompt=SYSTEM_PROMPT,
    state_schema=CopilotKitState,
    checkpointer=MemorySaver(),
)

app = FastAPI()

# Endpoint AG-UI (POST /): recebe mensagens e devolve o stream de eventos.
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


@app.get("/images/{image_id}")
def get_image(image_id: str) -> FileResponse:
    """Serve as figuras geradas por run_python_analysis (ver imdb/images.py)."""
    path = image_path(image_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png")


def main():
    """Sobe o uvicorn."""
    uvicorn.run("main:app", host="0.0.0.0", port=8123, reload=True)


if __name__ == "__main__":
    main()
