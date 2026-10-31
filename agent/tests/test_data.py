import math

import pytest

from imdb.data import explode_column, parse_duration_minutes, resolve_column, resolve_numeric_column


@pytest.mark.parametrize(
    "text,expected",
    [("1h 38m", 98), ("2h", 120), ("45m", 45), ("10h 5m", 605)],
)
def test_parse_duration_minutes(text, expected):
    assert parse_duration_minutes(text) == expected


@pytest.mark.parametrize("text", [None, float("nan"), "", "bad"])
def test_parse_duration_minutes_invalid_is_nan(text):
    assert math.isnan(parse_duration_minutes(text))


def test_resolve_column_accepts_alias_and_real_name(movies):
    assert resolve_column("rating", movies) == "rating_imdb"
    assert resolve_column("rating_imdb", movies) == "rating_imdb"
    assert resolve_column("RUNTIME", movies) == "duration_minutes"


def test_resolve_column_unknown_raises(movies):
    with pytest.raises(ValueError, match="Unknown column"):
        resolve_column("nope", movies)


def test_resolve_numeric_column_rejects_text(movies):
    with pytest.raises(ValueError, match="not numeric"):
        resolve_numeric_column("director", movies)


def test_explode_column_splits_multi_valued_only(movies):
    exploded = explode_column(movies, "genre")
    assert len(exploded) == 8  # A:2 B:1 C:1 D:1 E:1 (NaN) F:2
    assert set(exploded["genre"].dropna()) == {"Action", "Drama", "Comedy"}
    assert len(explode_column(movies, "year")) == len(movies)
