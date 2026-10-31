"""Pandas-backed tools for analyzing the IMDB top-movies-per-year dataset.

Two tools (`plot_chart`, `analyze_data`) are fixed, parameterized pandas
aggregations: `plot_chart` returns structured chart JSON (never a rendered
image) so the frontend can paint a real, interactive chart via CopilotKit
Generative UI. A third tool, `run_python_analysis`, runs a short model-written
Python snippet against the full dataframe in a restricted namespace (no
filesystem, network, or process access) for analysis the fixed tools don't
cover -- it is a deliberate, narrow exception to "never execute model-written
code", scoped to local development use only.
"""

import builtins
import contextlib
import io
import json
import threading
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
from langchain_core.tools import tool

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "world_imdb_movies_top_movies_per_year.csv"

# Friendly synonyms for the dataset's own (already clean) column names.
COLUMN_ALIASES: dict[str, str] = {
    "rating": "rating_imdb",
    "votes": "vote",
    "revenue": "gross_world_wide",
    "box_office": "gross_world_wide",
    "worldwide_gross": "gross_world_wide",
    "domestic_gross": "gross_us_canada",
    "opening_weekend": "gross_opening_weekend",
    "country": "country_origin",
    "location": "filming_location",
    "studio": "production_company",
    "mpa_rating": "rating_mpa",
}

# Which formatter the frontend should use for a given y_field.
CURRENCY_FIELDS = {"budget", "gross_world_wide", "gross_us_canada", "gross_opening_weekend"}
RATING_FIELDS = {"rating_imdb"}


@lru_cache(maxsize=1)
def load_dataframe() -> pd.DataFrame:
    """Load (and cache) the IMDB top-movies-per-year dataframe."""
    return pd.read_csv(DATA_PATH)


def _resolve_column(name: str, df: pd.DataFrame) -> str:
    if name in df.columns:
        return name
    alias = COLUMN_ALIASES.get(name.strip().lower())
    if alias and alias in df.columns:
        return alias
    raise ValueError(
        f"Unknown column '{name}'. Use one of the friendly aliases "
        f"{list(COLUMN_ALIASES)} or an exact dataframe column name "
        "(see the list_columns tool)."
    )


def _apply_filters(df: pd.DataFrame, filters: Optional[dict]) -> pd.DataFrame:
    if not filters:
        return df
    filtered = df
    for key, value in filters.items():
        col = _resolve_column(key, filtered)
        values = value if isinstance(value, list) else [value]
        filtered = filtered[filtered[col].isin(values)]
    return filtered


def _value_format(y_field: str) -> str:
    if y_field in CURRENCY_FIELDS:
        return "currency_usd"
    if y_field in RATING_FIELDS:
        return "rating"
    return "number"


@tool
def list_columns() -> str:
    """List the friendly field aliases and the raw dataframe columns available
    for the IMDB top-movies dataset. Call this first when you are unsure which
    column name to use for x_field, y_field, group_by, or a filter key."""
    df = load_dataframe()
    return json.dumps(
        {"aliases": COLUMN_ALIASES, "raw_columns": list(df.columns)},
        ensure_ascii=False,
    )


@tool
def plot_chart(
    chart_type: Literal["bar", "line", "pie"],
    x_field: str,
    y_field: str = "rating_imdb",
    group_by: Optional[str] = None,
    agg: Literal["sum", "mean", "count", "max", "min"] = "mean",
    filters: Optional[dict] = None,
    title: Optional[str] = None,
    top_n: int = 15,
) -> str:
    """Compute an aggregation over the IMDB movies dataframe and return
    STRUCTURED CHART DATA as JSON (never an image). The frontend renders this
    JSON as a real, interactive bar/line/pie chart.

    Args:
        chart_type: "bar", "line", or "pie".
        x_field: category/x-axis column or alias, e.g. "year", "genre",
            "country_origin", "director", "production_company".
        y_field: numeric column or alias to aggregate, e.g. "rating_imdb"
            (default), "vote", "budget", "gross_world_wide", "win",
            "nomination", "oscar".
        group_by: optional second categorical column/alias that splits each
            x-axis bucket into multiple series (ignored for chart_type="pie").
        agg: aggregation applied to y_field within each group. Defaults to
            "mean", which is almost always what you want for "rating_imdb";
            use "sum" for money fields like "gross_world_wide" or "budget".
        filters: optional {column_or_alias: value_or_[values]} to filter rows
            before aggregating, e.g. {"year": [2020, 2021], "genre": "Comedy"}.
            Matches are exact, so filter by the value as it literally appears
            in the data (see list_columns / analyze_data / run_python_analysis
            to inspect real values first, e.g. "genre" holds comma-joined
            multi-genre strings like "Action, Adventure, Sci-Fi").
        title: optional chart title; a sensible default is generated otherwise.
        top_n: caps the number of x-axis categories kept, ranked by total
            y_field size, so very wide breakdowns stay readable.
    """
    df = load_dataframe()
    x_col = _resolve_column(x_field, df)
    y_col = _resolve_column(y_field, df)
    group_col = _resolve_column(group_by, df) if group_by else None

    filtered = _apply_filters(df, filters)
    if filtered.empty:
        return json.dumps({"error": "No rows match the given filters."}, ensure_ascii=False)

    group_cols = [x_col] + ([group_col] if group_col else [])
    if agg == "count":
        grouped = filtered.groupby(group_cols, dropna=False).size().reset_index(name="value")
    else:
        grouped = filtered.groupby(group_cols, dropna=False)[y_col].agg(agg).reset_index(name="value")

    totals = grouped.groupby(x_col)["value"].sum().sort_values(ascending=False)
    keep = set(totals.head(top_n).index)
    grouped = grouped[grouped[x_col].isin(keep)]

    def _label(value: object) -> str:
        return "N/A" if pd.isna(value) else str(value)

    categories = sorted({_label(v) for v in grouped[x_col]})

    if group_col and chart_type != "pie":
        series = []
        for g_value, g_df in grouped.groupby(group_col, dropna=False):
            lookup = {_label(k): v for k, v in zip(g_df[x_col], g_df["value"])}
            series.append(
                {
                    "name": _label(g_value),
                    "data": [round(float(lookup.get(c, 0)), 2) for c in categories],
                }
            )
    else:
        lookup = {_label(k): v for k, v in zip(grouped[x_col], grouped.groupby(x_col)["value"].sum())}
        series = [
            {
                "name": y_field,
                "data": [round(float(lookup.get(c, 0)), 2) for c in categories],
            }
        ]

    chart = {
        "type": chart_type,
        "title": title
        or f"{agg} of {y_field} by {x_field}" + (f" and {group_by}" if group_by and chart_type != "pie" else ""),
        "categories": categories,
        "series": series,
        "value_format": _value_format(y_col),
    }
    return json.dumps(chart, ensure_ascii=False)


@tool
def analyze_data(
    x_field: str = "year",
    y_field: str = "rating_imdb",
    filters: Optional[dict] = None,
) -> str:
    """Return a short textual statistical summary (count, total, mean, min,
    max) of y_field grouped by x_field, after applying optional filters, over
    the IMDB movies dataframe. Use this for a written analysis instead of (or
    alongside) a chart."""
    df = load_dataframe()
    x_col = _resolve_column(x_field, df)
    y_col = _resolve_column(y_field, df)

    filtered = _apply_filters(df, filters)
    if filtered.empty:
        return "No rows match the given filters."

    stats = filtered.groupby(x_col, dropna=False)[y_col].agg(["count", "sum", "mean", "min", "max"]).round(2)
    top = stats.sort_values("sum", ascending=False).head(10)

    lines = [f"Summary of {y_field} by {x_field} (top {len(top)} groups by total, of {len(stats)}):"]
    for idx, row in top.iterrows():
        label = "N/A" if pd.isna(idx) else idx
        lines.append(
            f"- {label}: count={int(row['count'])}, total={row['sum']:.2f}, "
            f"mean={row['mean']:.2f}, min={row['min']:.2f}, max={row['max']:.2f}"
        )
    return "\n".join(lines)


_SAFE_BUILTIN_NAMES = (
    "len", "range", "sum", "min", "max", "sorted", "enumerate", "zip", "map",
    "filter", "round", "abs", "str", "int", "float", "bool", "list", "dict",
    "set", "tuple", "print", "isinstance", "type", "any", "all", "reversed",
)
_EXEC_TIMEOUT_SECONDS = 10
_MAX_RESULT_ROWS = 50


@tool
def run_python_analysis(code: str) -> str:
    """Run a short Python snippet for ad-hoc analysis the other tools don't
    cover (e.g. correlations, custom multi-column groupings, top-N by more
    than one criterion, value_counts on a messy field like "genre").

    The full IMDB dataframe is already loaded as `df` (a pandas.DataFrame),
    and `pd` (pandas) is available. Assign your final answer to a variable
    named `result` (a number, string, dict, list, pandas Series, or pandas
    DataFrame) and/or `print(...)` intermediate output -- both are returned
    to you. Do not reassign `df` to anything other than a view/copy derived
    from the original dataframe.

    This runs in a restricted sandbox with no file, network, process, or
    import access (only `pd`, `df`, and a few safe builtins are available),
    and is killed after 10 seconds -- keep snippets short and operate on
    aggregates, not the full 33k-row dataframe printed in full.

    Never use this tool to produce a chart for the user -- only `plot_chart`'s
    structured output is rendered by the frontend; a chart "drawn" with this
    tool (e.g. via matplotlib) will not be shown.
    """
    df = load_dataframe().copy()
    safe_builtins = {name: getattr(builtins, name) for name in _SAFE_BUILTIN_NAMES}
    namespace: dict[str, object] = {"__builtins__": safe_builtins, "pd": pd, "df": df, "result": None}
    stdout = io.StringIO()
    outcome: dict[str, str] = {}

    def _run() -> None:
        try:
            with contextlib.redirect_stdout(stdout):
                exec(code, namespace)  # noqa: S102 -- restricted namespace, local dev tool only
        except Exception as exc:  # noqa: BLE001 -- surfaced to the agent, not raised
            outcome["error"] = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=_EXEC_TIMEOUT_SECONDS)
    if thread.is_alive():
        return (
            f"Execution timed out after {_EXEC_TIMEOUT_SECONDS} seconds. "
            "Operate on a smaller slice or a pre-aggregated view of df and try again."
        )

    parts: list[str] = []
    printed = stdout.getvalue().strip()
    if printed:
        parts.append(printed)

    if "error" in outcome:
        parts.append(f"Error: {outcome['error']}")
    else:
        result = namespace.get("result")
        if result is not None:
            if isinstance(result, (pd.DataFrame, pd.Series)):
                parts.append(result.to_string(max_rows=_MAX_RESULT_ROWS))
            else:
                try:
                    parts.append(json.dumps(result, ensure_ascii=False, default=str))
                except TypeError:
                    parts.append(str(result))

    if not parts:
        return "The code ran with no printed output and no `result` variable set."
    return "\n\n".join(parts)
