"""Dataframe pequeno, escrito à mão, para testar as funções puras sem o CSV."""

import pandas as pd
import pytest

from imdb.data import parse_duration_minutes


@pytest.fixture
def movies() -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "title": ["A", "B", "C", "D", "E", "F"],
            "year": [2010, 2010, 2011, 2012, 2012, 2012],
            "rating_imdb": [8.0, 6.0, 7.0, 5.0, None, 9.0],
            "vote": [1000, 200, 500, 50, 10, 3000],
            "gross_world_wide": [500.0, None, 300.0, None, 20.0, 900.0],
            "genre": ["Action, Drama", "Drama", "Comedy", "Action", None, "Action, Comedy"],
            "director": ["X", "Y", "X", "Z", "Z", "X"],
            "duration": ["1h 30m", "2h", "45m", None, "bad", "1h 59m"],
            "oscar": [1, 0, 0, 0, 0, 2],
        }
    )
    df["duration_minutes"] = df["duration"].map(parse_duration_minutes)
    return df
