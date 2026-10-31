import json

import pytest

from imdb import charts


def aggregate(movies, **overrides):
    params = dict(
        chart_type="bar", x_field="genre", y_field="rating", group_by=None, agg="mean",
        filters=None, title=None, top_n=15, min_count=1,
    )
    params.update(overrides)
    return charts.aggregate_chart(movies, **params)


def test_genre_is_split_and_ranked_by_value(movies):
    chart = aggregate(movies)
    values = dict(zip(chart["categories"], chart["series"][0]["data"]))
    # Action: A(8), D(5), F(9) -> 7.33; Drama: A(8), B(6) -> 7; Comedy: C(7), F(9) -> 8
    assert values == {"Comedy": 8.0, "Action": 7.33, "Drama": 7.0}
    assert chart["categories"] == ["Comedy", "Action", "Drama"]  # maior para menor


def test_missing_values_are_left_out_and_reported(movies):
    chart = aggregate(movies, x_field="year", chart_type="line")
    assert chart["categories"] == ["2010", "2011", "2012"]  # ordem natural na linha
    assert any("no rating_imdb" in note for note in chart["notes"])
    json.dumps(chart, allow_nan=False)  # sem NaN


def test_top_n_ranks_by_aggregated_value_not_sum(movies):
    chart = aggregate(movies, top_n=1)
    assert chart["categories"] == ["Comedy"]


def test_min_count_drops_small_groups(movies):
    chart = aggregate(movies, x_field="director", min_count=3)
    assert chart["categories"] == ["X"]


def test_count_aggregation_ignores_y_field(movies):
    chart = aggregate(movies, x_field="year", agg="count", chart_type="line")
    assert chart["series"] == [{"name": "count", "data": [2, 1, 3]}]
    assert chart["value_format"] == "number"


def test_group_by_builds_one_series_per_group(movies):
    chart = aggregate(movies, x_field="year", group_by="director", agg="count", chart_type="line")
    assert {s["name"] for s in chart["series"]} == {"X", "Y", "Z"}
    for series in chart["series"]:
        assert len(series["data"]) == len(chart["categories"])


def test_aggregate_errors(movies):
    with pytest.raises(ValueError, match="No rows match"):
        aggregate(movies, filters={"year": 1900})
    with pytest.raises(ValueError, match="not numeric"):
        aggregate(movies, y_field="director")
    with pytest.raises(ValueError, match="min_count"):
        aggregate(movies, min_count=99)


def test_histogram_counts_add_up(movies):
    chart = charts.histogram_chart(movies, "rating", bins=4, filters=None, title=None)
    assert chart["type"] == "bar"
    assert len(chart["categories"]) == 4
    assert sum(chart["series"][0]["data"]) == 5  # 5 filmes têm nota


def test_scatter_points_and_correlation_note(movies):
    chart = charts.scatter_chart(movies, "rating", "votes", filters=None, title=None)
    assert chart["type"] == "scatter"
    assert len(chart["points"]) == 5
    assert chart["points"][0] == {"x": 8.0, "y": 1000.0, "label": "A (2010)"}
    assert "Pearson" in chart["notes"][0]


def test_scatter_samples_when_too_many_points(movies, monkeypatch):
    monkeypatch.setattr(charts, "MAX_SCATTER_POINTS", 2)
    chart = charts.scatter_chart(movies, "rating", "votes", filters=None, title=None)
    assert len(chart["points"]) == 2
    assert any("sampled" in note for note in chart["notes"])


def test_top_movies_descending_and_ascending(movies):
    top = charts.top_movies_chart(movies, "revenue", n=2, ascending=False, filters=None, title=None)
    assert top["categories"] == ["F (2012)", "A (2010)"]
    assert top["series"][0]["data"] == [900.0, 500.0]
    low = charts.top_movies_chart(movies, "revenue", n=1, ascending=True, filters=None, title=None)
    assert low["categories"] == ["E (2012)"]
    assert low["value_format"] == "currency_usd"
