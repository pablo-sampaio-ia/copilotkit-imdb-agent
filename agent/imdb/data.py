"""Carga do CSV e conhecimento sobre as colunas (nomes, apelidos, tipos).

Tudo que depende da *forma* dos dados fica aqui; os outros módulos só chamam
`load_dataframe()` e `resolve_column()`.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "world_imdb_movies_top_movies_per_year.csv"
)

# Apelidos amigáveis para os nomes reais das colunas.
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
    "runtime": "duration_minutes",
    "minutes": "duration_minutes",
}

# Colunas cujo valor é uma lista escrita como "A, B, C". Para agrupar ou
# filtrar por elas, cada elemento é tratado separadamente (ver `explode_column`
# e filters.py).
MULTI_VALUED_COLUMNS = {
    "genre",
    "star",
    "writer",
    "director",
    "country_origin",
    "language",
    "production_company",
}
LIST_SEPARATOR = ", "

# Qual formatador de números o front-end deve usar para cada coluna.
CURRENCY_COLUMNS = {"budget", "gross_world_wide", "gross_us_canada", "gross_opening_weekend"}
RATING_COLUMNS = {"rating_imdb"}


def parse_duration_minutes(text: object) -> float:
    """'1h 38m' -> 98.0; '2h' -> 120.0; '45m' -> 45.0; vazio/inválido -> NaN."""
    if not isinstance(text, str):
        return float("nan")
    hours = minutes = 0
    found = False
    for part in text.split():
        if part.endswith("h") and part[:-1].isdigit():
            hours, found = int(part[:-1]), True
        elif part.endswith("m") and part[:-1].isdigit():
            minutes, found = int(part[:-1]), True
    return float(hours * 60 + minutes) if found else float("nan")


@lru_cache(maxsize=1)
def load_dataframe() -> pd.DataFrame:
    """Lê o CSV uma única vez e acrescenta a coluna numérica `duration_minutes`."""
    df = pd.read_csv(DATA_PATH)
    df["duration_minutes"] = df["duration"].map(parse_duration_minutes)
    return df


def resolve_column(name: str, df: pd.DataFrame) -> str:
    """Aceita o nome real da coluna ou um apelido; levanta ValueError se não existir."""
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


def resolve_numeric_column(name: str, df: pd.DataFrame) -> str:
    """Como `resolve_column`, mas exige uma coluna numérica."""
    col = resolve_column(name, df)
    if not pd.api.types.is_numeric_dtype(df[col]):
        raise ValueError(f"Column '{col}' is not numeric; pick a numeric column such as rating_imdb, vote, budget.")
    return col


def explode_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Para colunas multivaloradas, gera uma linha por elemento (um filme com
    3 gêneros vira 3 linhas). Para as demais, devolve o dataframe como está."""
    if col not in MULTI_VALUED_COLUMNS:
        return df
    split = df[col].str.split(LIST_SEPARATOR)
    return df.assign(**{col: split}).explode(col)


def value_format(col: str) -> str:
    """Nome do formatador usado pelo front-end: currency_usd, rating ou number."""
    if col in CURRENCY_COLUMNS:
        return "currency_usd"
    if col in RATING_COLUMNS:
        return "rating"
    return "number"


def describe_columns(df: pd.DataFrame) -> dict:
    """Resumo das colunas, devolvido pela ferramenta `list_columns`."""
    return {
        "aliases": COLUMN_ALIASES,
        "raw_columns": list(df.columns),
        "numeric_columns": [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])],
        "multi_valued_columns": sorted(MULTI_VALUED_COLUMNS),
        "missing_share": {c: round(float(v), 2) for c, v in df.isna().mean().items() if v > 0.05},
        "notes": [
            "Multi-valued columns hold lists like 'Action, Drama'; grouping and filtering treat each element separately.",
            "duration is text ('1h 38m'); use duration_minutes (alias runtime) for numbers.",
            "Money columns mix currencies and have many missing values; treat them with care.",
        ],
    }
