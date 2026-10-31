# IMDB Movies Analysis Agent

Um agente LangGraph (Python) exposto por AG-UI, com um front-end Next.js +
CopilotKit, para explorar o dataset IMDB top-movies-per-year em linguagem
natural. Peça um gráfico, um resumo ou uma análise sob medida; o agente chama
ferramentas baseadas em pandas e responde a partir dos dados reais.

## Funcionalidades

- **Chat** lateral do CopilotKit, com sugestões clicáveis.
- **Gráficos interativos** no próprio chat: barras, linha, pizza, histograma,
  dispersão (rating × votos) e top-N de filmes individuais.
- **Human-in-the-loop**: para pedidos amplos, o agente pede confirmação
  (`confirm_chart_spec`) antes de gerar o gráfico.
- **Análise sob medida**: `run_python_analysis` roda um trecho de Python sobre o
  dataframe; pode devolver texto e uma **imagem estática** (matplotlib).
- **Threads persistentes e Inspector** (opcional): via CopilotKit Intelligence.

## Arquitetura

```
Navegador (React)  ──HTTP/SSE──►  Next.js /api/copilotkit  ──AG-UI──►  Python (FastAPI :8123)
 chat + gráficos                  CopilotRuntime + HttpAgent           LangGraph + ferramentas pandas
```

AG-UI é um protocolo de eventos (texto, chamadas de ferramenta, resultados,
estado) entre o agente e a interface. O agente emite uma chamada de ferramenta
e seu resultado; o front-end registra *renderizadores* que transformam esse
resultado em componentes React (gráfico, cartão de código, botões de
confirmação).

## Mapa de leitura

1. `agent/README.md` e `agent/main.py`: o agente e suas ferramentas.
2. `app/api/copilotkit/[[...slug]]/route.ts`: o runtime que liga navegador e agente
   (e escolhe entre modo Intelligence e modo local).
3. `app/layout.tsx`: o `<CopilotKit>`, que dá a conexão a toda a árvore React.
4. `app/page.tsx` → `components/HomeLayout.tsx`: a tela (threads, painel, chat).
5. `components/CopilotDataTools.tsx` e `components/tools/`: cada ferramenta do
   agente ligada à sua interface (`useRenderTool`, `useHumanInTheLoop`).
6. `components/generative-ui/`: os componentes que desenham gráficos, imagem e confirmação.

## Rodando

Dois terminais:

```bash
# Terminal 1: o agente Python
cd agent
cp .env.example .env     # preencha OPENAI_API_KEY
uv run python main.py

# Terminal 2: o front-end
npm install
npm run dev
```

Abra http://localhost:3000.

Comandos úteis: `npm run check-types`, `npm run lint`, `npm test` (pytest do agente).

## CopilotKit Intelligence (opcional) e custo de dependência

O Intelligence é o serviço gerenciado do CopilotKit. **Com** `CPK_INTELLIGENCE_API_KEY`
no `.env` da raiz, você tem threads persistentes (lista de conversas), o
Inspector e o Automatic Learning. **Sem** a chave, o app roda em modo local:
o chat, os gráficos e a análise funcionam normalmente, mas as conversas ficam
só em memória (somem ao recarregar) e não há lista de conversas nem Inspector.

O que isso significa para o projeto: threads e histórico vivem na nuvem do
CopilotKit, então ficar com o Intelligence é uma dependência de serviço
externo. Para evoluir sem ela, o caminho é um `runner` próprio no
`CopilotRuntime` (por exemplo, com persistência em SQLite).

## Configuração

| Variável | Onde | Para quê |
|---|---|---|
| `OPENAI_API_KEY` | `agent/.env` | Modelo do agente (obrigatória; o agente avisa na partida se faltar). |
| `COPILOTKIT_AGENT_MODEL` | `agent/.env` | Opcional; `<provedor>:<modelo>`, padrão `openai:gpt-4.1-mini`. |
| `CPK_INTELLIGENCE_API_KEY` | `.env` | Opcional; liga o modo Intelligence. |
| `IMDB_AGENT_URL` | `.env` | Opcional; padrão `http://localhost:8123`. |

## Fora do escopo desta versão

Sandbox endurecido para o Python do modelo, persistência do estado do grafo,
estado compartilhado agente↔UI, gráficos fixados em painel e edição da
especificação na confirmação.
