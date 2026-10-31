# Agente IMDB (Python)

Agente LangGraph exposto por AG-UI (FastAPI, porta 8123). Responde perguntas
sobre `../data/world_imdb_movies_top_movies_per_year.csv` chamando ferramentas
baseadas em pandas.

## Ordem de leitura

| Arquivo | O que tem |
|---|---|
| `main.py` | Monta o grafo (`create_agent`) e o endpoint AG-UI. Começa por aqui. |
| `imdb/prompt.py` | System prompt: só a política (quando confirmar, como responder). |
| `imdb/tools.py` | As ferramentas que o LLM enxerga. As **docstrings** são a documentação delas para o modelo. |
| `imdb/data.py` | Carga do CSV, apelidos de coluna, colunas multivaloradas, duração em minutos. |
| `imdb/filters.py` | Filtros em JSON (`{"year": {"gte": 2010}}`). |
| `imdb/charts.py` | Especificações de gráfico (bar, line, pie, histograma, dispersão, top filmes). |
| `imdb/summary.py` | Resumo estatístico em texto. |
| `imdb/python_sandbox.py` | Executa trechos de Python do modelo; pode gerar uma figura. |
| `imdb/images.py` | Guarda os PNGs das figuras em `.cache/images/`. |
| `imdb/config.py` | Variáveis de ambiente e validação na partida. |
| `tests/` | Testes pytest das funções puras (`uv run pytest`). |

## Como uma ferramenta de gráfico funciona

1. O LLM chama, por exemplo, `plot_chart(chart_type="bar", x_field="genre", ...)`.
2. `charts.py` filtra, agrega com pandas e devolve um dict; `tools.py` o
   converte em JSON (erros previstos viram `{"error": "..."}` para o modelo se corrigir).
3. O JSON viaja como resultado da ferramenta (AG-UI `TOOL_CALL_RESULT`) até o
   navegador, que o desenha (`components/generative-ui/ChartRenderer.tsx`).

Nenhuma imagem é gerada nesse caminho, e é por isso que os gráficos são interativos.

## Imagens de `run_python_analysis`

Se o código do modelo desenha com `plt`, a figura vira PNG em
`.cache/images/<id>.png`. O resultado da ferramenta leva só o `image_id`
(um PNG em base64 custaria dezenas de milhares de tokens de contexto). O
navegador busca o PNG em `GET /images/{id}` (via o proxy
`app/api/analysis-images/[id]/route.ts`).

## Limitações conhecidas (versão de teste)

- `run_python_analysis` limita o namespace e o tempo, mas **não é um sandbox de
  segurança**: `pd.read_csv("arquivo")` ainda lê arquivos. Uso local apenas.
- O estado do grafo (`MemorySaver`) fica em memória; reiniciar o agente o apaga.
- As colunas de dinheiro misturam moedas e têm muitos valores faltantes.

## Rodando

```bash
cp .env.example .env   # preencha OPENAI_API_KEY
uv run python main.py  # porta 8123, com reload
uv run pytest          # testes
```
