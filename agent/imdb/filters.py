"""Filtros declarativos em JSON, aplicados a um dataframe.

Formato aceito (a chave é uma coluna ou apelido):

    {"year": 2020}                            # igualdade
    {"genre": ["Comedy", "Drama"]}            # qualquer um dos valores
    {"year": {"gte": 2010, "lt": 2020}}       # operadores (todos precisam valer)
    {"title": {"contains": "star"}}           # texto contido (sem diferenciar maiúsculas)

Operadores: eq, ne, in, gt, gte, lt, lte, contains.
Em colunas multivaloradas ("Action, Drama") eq/ne/in olham cada elemento.
"""

from typing import Any, Callable, Optional

import pandas as pd

from .data import LIST_SEPARATOR, MULTI_VALUED_COLUMNS, resolve_column

OPERATORS = ("eq", "ne", "in", "gt", "gte", "lt", "lte", "contains")


def _coerce(series: pd.Series, value: Any) -> Any:
    """O LLM às vezes manda '2015' (texto) para uma coluna numérica."""
    if pd.api.types.is_numeric_dtype(series) and isinstance(value, str):
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Expected a number to compare with a numeric column, got '{value}'.") from exc
    return value


def _is_in(series: pd.Series, col: str, values: list) -> pd.Series:
    if col in MULTI_VALUED_COLUMNS:
        wanted = {str(v) for v in values}
        return series.fillna("").map(lambda cell: bool(wanted & set(cell.split(LIST_SEPARATOR))))
    return series.isin([_coerce(series, v) for v in values])


def _mask_for_operator(series: pd.Series, col: str, op: str, value: Any) -> pd.Series:
    if op not in OPERATORS:
        raise ValueError(f"Unknown filter operator '{op}'. Valid operators: {list(OPERATORS)}.")
    if op == "eq":
        return _is_in(series, col, [value])
    if op == "ne":
        return ~_is_in(series, col, [value])
    if op == "in":
        return _is_in(series, col, value if isinstance(value, list) else [value])
    if op == "contains":
        return series.astype(str).str.contains(str(value), case=False, na=False, regex=False)
    compare: dict[str, Callable[[pd.Series, Any], pd.Series]] = {
        "gt": lambda s, v: s > v,
        "gte": lambda s, v: s >= v,
        "lt": lambda s, v: s < v,
        "lte": lambda s, v: s <= v,
    }
    return compare[op](series, _coerce(series, value))


def apply_filters(df: pd.DataFrame, filters: Optional[dict]) -> pd.DataFrame:
    """Aplica todas as condições (E lógico) e devolve o dataframe filtrado."""
    if not filters:
        return df
    for key, condition in filters.items():
        col = resolve_column(key, df)
        if isinstance(condition, dict):
            mask = pd.Series(True, index=df.index)
            for op, value in condition.items():
                mask &= _mask_for_operator(df[col], col, op, value)
        elif isinstance(condition, list):
            mask = _mask_for_operator(df[col], col, "in", condition)
        else:
            mask = _mask_for_operator(df[col], col, "eq", condition)
        df = df[mask]
    return df
