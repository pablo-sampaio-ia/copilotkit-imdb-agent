"""Resumo estatístico em texto (count/total/mean/min/max) agrupado por um campo."""

from typing import Optional

import pandas as pd

from .data import explode_column, resolve_column, resolve_numeric_column
from .filters import apply_filters

TOP_GROUPS = 10


def summarize(df: pd.DataFrame, x_field: str, y_field: str, filters: Optional[dict]) -> str:
    x_col = resolve_column(x_field, df)
    y_col = resolve_numeric_column(y_field, df)

    rows = explode_column(apply_filters(df, filters), x_col).dropna(subset=[x_col])
    if rows.empty:
        return "No rows match the given filters."

    missing = int(rows[y_col].isna().sum())
    stats = rows.groupby(x_col)[y_col].agg(["count", "sum", "mean", "min", "max"]).round(2)
    top = stats.sort_values("sum", ascending=False).head(TOP_GROUPS)

    lines = [f"Summary of {y_field} by {x_field} (top {len(top)} groups by total, of {len(stats)}):"]
    for label, row in top.iterrows():
        lines.append(
            f"- {label}: count={int(row['count'])}, total={row['sum']:.2f}, "
            f"mean={row['mean']:.2f}, min={row['min']:.2f}, max={row['max']:.2f}"
        )
    if missing:
        lines.append(f"Note: {missing} of {len(rows)} rows have no {y_col} and are not counted.")
    return "\n".join(lines)
