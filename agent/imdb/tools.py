"""Ferramentas (`@tool`) que o agente LangGraph pode chamar.

Este arquivo é só a "casca": cada ferramenta valida nada além do necessário e
delega a lógica para data.py / filters.py / charts.py / summary.py /
python_sandbox.py. As DOCSTRINGS são a fonte única de documentação das
ferramentas para o LLM (o system prompt, em prompt.py, só traz a política).

Convenção de retorno:
- ferramentas de gráfico devolvem JSON da especificação (ver charts.py);
- em caso de erro previsto (coluna inexistente, filtro sem linhas...) devolvem
  {"error": "..."} para o modelo poder corrigir a chamada, em vez de quebrar.
"""

import json
from functools import wraps
from typing import Callable, Literal, Optional

from langchain_core.tools import tool

from . import charts
from .data import describe_columns, load_dataframe
from .python_sandbox import run_snippet
from .summary import summarize


def _to_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False)


def reports_errors_as_json(func: Callable[..., dict]) -> Callable[..., str]:
    """Converte o dict devolvido em JSON e ValueError em {"error": ...}."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> str:
        try:
            return _to_json(func(*args, **kwargs))
        except ValueError as exc:
            return _to_json({"error": str(exc)})

    return wrapper


@tool
def list_columns() -> str:
    """List the dataset's columns: friendly aliases, raw column names, which are
    numeric, which hold multi-valued lists (e.g. genre), and which have many
    missing values. Call this first when unsure which column name to use."""
    return _to_json(describe_columns(load_dataframe()))


@tool
@reports_errors_as_json
def plot_chart(
    chart_type: Literal["bar", "line", "pie"],
    x_field: str,
    y_field: str = "rating_imdb",
    group_by: Optional[str] = None,
    agg: Literal["sum", "mean", "count", "max", "min"] = "mean",
    filters: Optional[dict] = None,
    title: Optional[str] = None,
    top_n: int = 15,
    min_count: int = 1,
) -> dict:
    """Aggregate y_field by x_field and return STRUCTURED CHART DATA that the UI
    renders as an interactive bar, line, or pie chart (never an image). This is
    the way to show aggregated charts.

    Args:
        chart_type: "bar" (ranked categories), "line" (ordered x, e.g. year) or "pie".
        x_field: category / x-axis column or alias, e.g. "year", "genre", "country",
            "director". Multi-valued columns (genre, star, writer, director, country,
            language, production_company) count each element separately, so a
            movie with three genres contributes to three groups.
        y_field: numeric column or alias to aggregate, e.g. "rating_imdb" (default),
            "vote", "budget", "gross_world_wide", "win", "oscar", "runtime".
        group_by: optional second categorical column that splits each x bucket into
            several series (ignored for pie).
        agg: aggregation of y_field per group. "mean" suits ratings; use "sum" for
            money and "count" to count movies (y_field is then ignored).
        filters: optional row filter applied first. Filters are {column: value | [values] | {op: value}}
        with ops eq/ne/in/gt/gte/lt/lte/contains, e.g.
        {"year": {"gte": 2010}, "genre": "Comedy", "title": {"contains": "star"}}.
        title: optional chart title.
        top_n: keeps only the top_n categories, ranked by their aggregated value.
        min_count: drop x categories with fewer movies than this. Use e.g. 5 when
            ranking by "mean", so a single-movie group cannot top the chart.
    """
    return charts.aggregate_chart(
        load_dataframe(), chart_type, x_field, y_field, group_by, agg, filters, title, top_n, min_count
    )


@tool
@reports_errors_as_json
def plot_distribution(
    field: str,
    bins: int = 10,
    filters: Optional[dict] = None,
    title: Optional[str] = None,
    trim_outliers: bool = True,
) -> dict:
    """Histogram of a numeric field: how many movies fall in each equal-width
    range. Returns chart data the UI renders as bars.

    Args:
        field: numeric column or alias, e.g. "rating_imdb", "runtime", "year", "vote".
        bins: number of ranges (2-40).
        filters: optional row filter. Filters are {column: value | [values] | {op: value}}
        with ops eq/ne/in/gt/gte/lt/lte/contains, e.g.
        {"year": {"gte": 2010}, "genre": "Comedy", "title": {"contains": "star"}}.
        title: optional chart title.
        trim_outliers: leave out values beyond the 1st-99th percentile (default),
            so extreme values do not squash the chart. Set false to see them.
    """
    return charts.histogram_chart(load_dataframe(), field, bins, filters, title, trim_outliers)


@tool
@reports_errors_as_json
def plot_scatter(
    x_field: str,
    y_field: str,
    filters: Optional[dict] = None,
    title: Optional[str] = None,
) -> dict:
    """Scatter plot of two numeric fields, one point per movie (hover shows the
    title). The result includes the Pearson correlation in its notes. Use it to
    relate two measures, e.g. rating vs votes.

    Args:
        x_field: numeric column or alias for the x axis.
        y_field: numeric column or alias for the y axis.
        filters: optional row filter. Filters are {column: value | [values] | {op: value}}
        with ops eq/ne/in/gt/gte/lt/lte/contains, e.g.
        {"year": {"gte": 2010}, "genre": "Comedy", "title": {"contains": "star"}}.
        title: optional chart title.
    """
    return charts.scatter_chart(load_dataframe(), x_field, y_field, filters, title)


@tool
@reports_errors_as_json
def plot_top_movies(
    metric: str,
    n: int = 10,
    ascending: bool = False,
    filters: Optional[dict] = None,
    title: Optional[str] = None,
) -> dict:
    """Bar chart of the n individual movies with the highest (or lowest) value of
    a numeric metric, e.g. the 10 highest-grossing movies of the 2010s.

    Args:
        metric: numeric column or alias, e.g. "gross_world_wide", "rating_imdb", "vote", "oscar".
        n: how many movies (1-30).
        ascending: true for the lowest values instead of the highest.
        filters: optional row filter. Filters are {column: value | [values] | {op: value}}
        with ops eq/ne/in/gt/gte/lt/lte/contains, e.g.
        {"year": {"gte": 2010}, "genre": "Comedy", "title": {"contains": "star"}}.
        title: optional chart title.
    """
    return charts.top_movies_chart(load_dataframe(), metric, n, ascending, filters, title)


@tool
def analyze_data(
    x_field: str = "year",
    y_field: str = "rating_imdb",
    filters: Optional[dict] = None,
) -> str:
    """Short TEXT summary (count, total, mean, min, max) of numeric y_field grouped
    by x_field, for a written analysis instead of (or alongside) a chart.
    Multi-valued x fields (e.g. genre) count each element separately.

    Args:
        x_field: grouping column or alias.
        y_field: numeric column or alias.
        filters: optional row filter. Filters are {column: value | [values] | {op: value}}
        with ops eq/ne/in/gt/gte/lt/lte/contains, e.g.
        {"year": {"gte": 2010}, "genre": "Comedy", "title": {"contains": "star"}}.
    """
    try:
        return summarize(load_dataframe(), x_field, y_field, filters)
    except ValueError as exc:
        return f"Error: {exc}"


@tool
def run_python_analysis(code: str) -> str:
    """Run a short Python snippet for analysis the other tools do not cover
    (correlations, custom groupings, several criteria at once...).

    The dataframe is available as `df`, pandas as `pd` and matplotlib's pyplot as
    `plt`. Assign the final answer to `result` and/or print(). If you draw a
    figure with `plt`, it is shown to the user as a static PNG image (no
    interactivity), so only draw one when plot_chart / plot_distribution /
    plot_scatter / plot_top_movies cannot express it (e.g. a heatmap or a boxplot).

    Runs with a 10 second timeout and no imports; operate on aggregates rather
    than printing the whole 33k-row dataframe. Returns JSON:
    {"text": ..., "image_id": ... or null, "is_error": bool}.
    """
    return _to_json(dict(run_snippet(code, load_dataframe())))


ALL_TOOLS = [
    list_columns,
    plot_chart,
    plot_distribution,
    plot_scatter,
    plot_top_movies,
    analyze_data,
    run_python_analysis,
]
