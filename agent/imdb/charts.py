"""Construção das especificações de gráfico (dicts prontos para virar JSON).

Cada função recebe o dataframe + parâmetros e devolve um dict que o front-end
(components/generative-ui/ChartRenderer.tsx) sabe desenhar. Nenhuma imagem é
gerada aqui: o gráfico é desenhado no navegador, o que o torna interativo.

Formato comum:
    {"type": "bar" | "line" | "pie" | "scatter", "title": str,
     "notes": [str, ...], ...campos específicos do tipo...}

- bar/line/pie:  "categories": [str], "series": [{"name": str, "data": [num]}],
                 "value_format": "currency_usd" | "rating" | "number"
- scatter:       "points": [{"x", "y", "label"}], "x_label", "y_label",
                 "x_format", "y_format"
"""

from typing import Literal, Optional

import numpy as np
import pandas as pd

from .data import explode_column, resolve_column, resolve_numeric_column, value_format
from .filters import apply_filters

Aggregation = Literal["sum", "mean", "count", "max", "min"]

MAX_SERIES = 8  # séries (group_by) desenhadas por gráfico
MAX_SCATTER_POINTS = 500


def _num(value: float) -> float:
    return round(float(value), 2)


def _label(value: object) -> str:
    """Rótulo de categoria; números inteiros guardados como float viram '2015'."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _short_number(value: float) -> str:
    """5_600_000 -> '5.6M'; usado nos rótulos das faixas do histograma."""
    magnitude = abs(value)
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if magnitude >= limit:
            return f"{value / limit:.3g}{suffix}"
    return f"{value:.3g}"


def _movie_label(row: pd.Series) -> str:
    return f"{row['title']} ({row['year']})"


def aggregate_chart(
    df: pd.DataFrame,
    chart_type: Literal["bar", "line", "pie"],
    x_field: str,
    y_field: str,
    group_by: Optional[str],
    agg: Aggregation,
    filters: Optional[dict],
    title: Optional[str],
    top_n: int,
    min_count: int,
) -> dict:
    """Agrega `y_field` por `x_field` (e opcionalmente por `group_by`)."""
    x_col = resolve_column(x_field, df)
    group_col = resolve_column(group_by, df) if group_by and chart_type != "pie" else None
    y_col = None if agg == "count" else resolve_numeric_column(y_field, df)

    rows = apply_filters(df, filters)
    matched = len(rows)
    rows = explode_column(rows, x_col)
    if group_col and group_col != x_col:
        rows = explode_column(rows, group_col)

    group_cols = [x_col] + ([group_col] if group_col and group_col != x_col else [])
    rows = rows.dropna(subset=group_cols)
    notes: list[str] = []
    if y_col:
        before = len(rows)
        rows = rows.dropna(subset=[y_col])
        if before > len(rows):
            notes.append(f"{before - len(rows)} of {before} rows have no {y_col} and were left out.")
    if rows.empty:
        raise ValueError("No rows match the given filters (or all of them lack the requested field).")

    grouped = rows.groupby(group_cols)
    table = (grouped.size() if y_col is None else grouped[y_col].agg(agg)).rename("value").reset_index()

    # Só mantém categorias com pelo menos `min_count` filmes (evita que um
    # grupo de 1 filme lidere um ranking de médias).
    sizes = rows.groupby(x_col).size()
    table = table[table[x_col].isin(sizes[sizes >= min_count].index)]
    if table.empty:
        raise ValueError(f"No {x_field} category has at least {min_count} movies; lower min_count.")

    # Ranking das categorias: pela soma quando os valores são totais, pelo maior
    # valor quando são médias/extremos (somar médias não faz sentido).
    by_x = table.groupby(x_col)["value"]
    totals = by_x.sum() if agg in ("sum", "count") else by_x.max()
    ranked = totals.sort_values(ascending=False)
    if len(ranked) > top_n:
        notes.append(f"Showing the top {top_n} of {len(ranked)} categories.")
    keep = ranked.head(top_n).index
    table = table[table[x_col].isin(keep)]

    # Linha: ordem natural do eixo x (ex.: anos). Barra/pizza: maior para menor.
    order = sorted(keep) if chart_type == "line" else list(keep)
    categories = [_label(c) for c in order]

    if group_col and group_col != x_col:
        group_totals = table.groupby(group_col)["value"].sum().sort_values(ascending=False)
        if len(group_totals) > MAX_SERIES:
            notes.append(f"Showing the {MAX_SERIES} largest of {len(group_totals)} {group_by} groups.")
        series = []
        for group_value in group_totals.head(MAX_SERIES).index:
            part = table[table[group_col] == group_value]
            lookup = dict(zip(part[x_col], part["value"]))
            series.append({"name": _label(group_value), "data": [_num(lookup.get(c, 0)) for c in order]})
    else:
        lookup = totals.to_dict()
        name = "count" if y_col is None else y_field
        series = [{"name": name, "data": [_num(lookup[c]) for c in order]}]

    default_title = f"{agg} of {y_field if y_col else 'movies'} by {x_field}"
    if group_col and chart_type != "pie":
        default_title += f" and {group_by}"
    return {
        "type": chart_type,
        "title": title or default_title,
        "categories": categories,
        "series": series,
        "value_format": "number" if y_col is None else value_format(y_col),
        "notes": notes + ([f"{matched} movies matched the filters."] if filters else []),
    }


def histogram_chart(
    df: pd.DataFrame,
    field: str,
    bins: int,
    filters: Optional[dict],
    title: Optional[str],
    trim_outliers: bool = True,
) -> dict:
    """Distribuição de um campo numérico em faixas de mesma largura (devolvida como barras).

    Com `trim_outliers`, valores fora do intervalo entre os percentis 1 e 99 ficam de fora:
    sem isso, um único valor absurdo (ex.: uma minissérie de 4000 minutos) estica o
    eixo e faz quase todos os filmes caírem na primeira faixa."""
    col = resolve_numeric_column(field, df)
    values = apply_filters(df, filters)[col].dropna()
    if values.empty:
        raise ValueError(f"No rows with a value for {col} match the given filters.")

    notes = []
    if trim_outliers:
        low, high = values.quantile(0.01), values.quantile(0.99)
        kept = values[(values >= low) & (values <= high)]
        if len(kept) < len(values):
            notes.append(
                f"{len(values) - len(kept)} extreme values outside {_short_number(low)}–{_short_number(high)} left out."
            )
        values = kept

    counts, edges = np.histogram(values, bins=max(2, min(bins, 40)))
    categories = [f"{_short_number(edges[i])}–{_short_number(edges[i + 1])}" for i in range(len(counts))]
    return {
        "type": "bar",
        "title": title or f"Distribution of {field}",
        "categories": categories,
        "series": [{"name": "movies", "data": [int(c) for c in counts]}],
        "value_format": "number",
        "notes": [f"{len(values)} movies shown."] + notes,
    }


def scatter_chart(
    df: pd.DataFrame,
    x_field: str,
    y_field: str,
    filters: Optional[dict],
    title: Optional[str],
) -> dict:
    """Dispersão entre dois campos numéricos, um ponto por filme."""
    x_col = resolve_numeric_column(x_field, df)
    y_col = resolve_numeric_column(y_field, df)
    rows = apply_filters(df, filters).dropna(subset=[x_col, y_col])
    if rows.empty:
        raise ValueError("No rows with both fields present match the given filters.")

    notes = [f"{len(rows)} movies; Pearson correlation {_num(rows[x_col].corr(rows[y_col]))}."]
    if len(rows) > MAX_SCATTER_POINTS:
        rows = rows.sample(MAX_SCATTER_POINTS, random_state=0)
        notes.append(f"Randomly sampled {MAX_SCATTER_POINTS} points for readability.")

    points = [
        {"x": _num(r[x_col]), "y": _num(r[y_col]), "label": _movie_label(r)} for _, r in rows.iterrows()
    ]
    return {
        "type": "scatter",
        "title": title or f"{y_field} vs {x_field}",
        "x_label": x_field,
        "y_label": y_field,
        "x_format": value_format(x_col),
        "y_format": value_format(y_col),
        "points": points,
        "notes": notes,
    }


def top_movies_chart(
    df: pd.DataFrame,
    metric: str,
    n: int,
    ascending: bool,
    filters: Optional[dict],
    title: Optional[str],
) -> dict:
    """Os `n` filmes individuais com maior (ou menor) valor de `metric`."""
    col = resolve_numeric_column(metric, df)
    rows = apply_filters(df, filters).dropna(subset=[col])
    if rows.empty:
        raise ValueError(f"No rows with a value for {col} match the given filters.")

    n = max(1, min(n, 30))
    top = rows.nsmallest(n, col) if ascending else rows.nlargest(n, col)
    return {
        "type": "bar",
        "title": title or f"{'Lowest' if ascending else 'Top'} {len(top)} movies by {metric}",
        "categories": [_movie_label(r) for _, r in top.iterrows()],
        "series": [{"name": metric, "data": [_num(v) for v in top[col]]}],
        "value_format": value_format(col),
        "notes": [],
    }
