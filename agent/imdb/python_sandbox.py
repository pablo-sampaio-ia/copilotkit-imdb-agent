"""Execução de trechos de Python escritos pelo modelo, sobre o dataframe.

ATENÇÃO: isto é uma restrição de conveniência (namespace limitado + timeout),
NÃO um sandbox de segurança. Serve apenas para uso local de desenvolvimento.

O trecho enxerga `df`, `pd` (pandas), `plt` (matplotlib.pyplot) e alguns
builtins. Se criar uma figura, ela é salva como PNG (ver images.py) e o
resultado traz o `image_id`.
"""

import builtins
import contextlib
import io
import json
import threading
from typing import Optional, TypedDict

import matplotlib

matplotlib.use("Agg")  # sem janela; precisa vir antes de importar pyplot
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .images import save_png  # noqa: E402

SAFE_BUILTIN_NAMES = (
    "len", "range", "sum", "min", "max", "sorted", "enumerate", "zip", "map",
    "filter", "round", "abs", "str", "int", "float", "bool", "list", "dict",
    "set", "tuple", "print", "isinstance", "type", "any", "all", "reversed",
)
TIMEOUT_SECONDS = 10
MAX_RESULT_ROWS = 50

# O estado do pyplot é global; só uma execução por vez pode usá-lo.
_PLOT_LOCK = threading.Lock()


class SnippetResult(TypedDict):
    text: str
    image_id: Optional[str]
    is_error: bool


def _figure_to_image_id() -> Optional[str]:
    """Salva a figura atual (se houver) e fecha todas, para não vazar memória."""
    if not plt.get_fignums():
        return None
    buffer = io.BytesIO()
    plt.gcf().savefig(buffer, format="png", dpi=100, bbox_inches="tight")
    plt.close("all")
    return save_png(buffer.getvalue())


def _format_result(result: object) -> str:
    if isinstance(result, (pd.DataFrame, pd.Series)):
        return result.to_string(max_rows=MAX_RESULT_ROWS)
    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except TypeError:
        return str(result)


def run_snippet(code: str, df: pd.DataFrame) -> SnippetResult:
    """Executa `code` e devolve texto (prints + variável `result`) e imagem opcional."""
    safe_builtins = {name: getattr(builtins, name) for name in SAFE_BUILTIN_NAMES}
    namespace: dict[str, object] = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "plt": plt,
        "df": df.copy(),
        "result": None,
    }
    stdout = io.StringIO()
    outcome: dict[str, object] = {}

    def _run() -> None:
        with _PLOT_LOCK:
            try:
                with contextlib.redirect_stdout(stdout):
                    exec(code, namespace)  # noqa: S102 -- uso local, ver aviso no topo
                outcome["image_id"] = _figure_to_image_id()
            except Exception as exc:  # noqa: BLE001 -- vai para o agente, não é relançada
                outcome["error"] = f"{type(exc).__name__}: {exc}"
                plt.close("all")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=TIMEOUT_SECONDS)
    if thread.is_alive():
        return {
            "text": f"Execution timed out after {TIMEOUT_SECONDS} seconds. "
            "Operate on a smaller slice or a pre-aggregated view of df and try again.",
            "image_id": None,
            "is_error": True,
        }

    parts: list[str] = []
    printed = stdout.getvalue().strip()
    if printed:
        parts.append(printed)
    if "error" in outcome:
        parts.append(f"Error: {outcome['error']}")
    elif namespace.get("result") is not None:
        parts.append(_format_result(namespace["result"]))

    image_id = outcome.get("image_id")
    if image_id:
        parts.append("A chart image was produced and is shown to the user.")
    if not parts:
        parts.append("The code ran with no printed output, no `result` variable and no figure.")
    return {
        "text": "\n\n".join(parts),
        "image_id": image_id if isinstance(image_id, str) else None,
        "is_error": "error" in outcome,
    }
