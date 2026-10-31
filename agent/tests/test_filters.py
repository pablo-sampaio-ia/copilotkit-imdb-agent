import pytest

from imdb.filters import apply_filters


def titles(df):
    return list(df["title"])


def test_no_filters_returns_everything(movies):
    assert len(apply_filters(movies, None)) == len(movies)
    assert len(apply_filters(movies, {})) == len(movies)


def test_equality_scalar_and_list(movies):
    assert titles(apply_filters(movies, {"year": 2011})) == ["C"]
    assert titles(apply_filters(movies, {"year": [2010, 2011]})) == ["A", "B", "C"]


def test_string_number_is_coerced(movies):
    assert titles(apply_filters(movies, {"year": "2011"})) == ["C"]


def test_range_operators(movies):
    assert titles(apply_filters(movies, {"year": {"gte": 2011, "lt": 2012}})) == ["C"]
    assert titles(apply_filters(movies, {"rating": {"gt": 7}})) == ["A", "F"]


def test_multi_valued_equality_matches_any_element(movies):
    assert titles(apply_filters(movies, {"genre": "Action"})) == ["A", "D", "F"]
    assert titles(apply_filters(movies, {"genre": ["Drama", "Comedy"]})) == ["A", "B", "C", "F"]


def test_not_equal_on_multi_valued(movies):
    assert titles(apply_filters(movies, {"genre": {"ne": "Action"}})) == ["B", "C", "E"]


def test_contains_is_case_insensitive(movies):
    assert titles(apply_filters(movies, {"genre": {"contains": "comed"}})) == ["C", "F"]


def test_conditions_combine_with_and(movies):
    assert titles(apply_filters(movies, {"genre": "Action", "year": 2012})) == ["D", "F"]


def test_unknown_operator_raises(movies):
    with pytest.raises(ValueError, match="Unknown filter operator"):
        apply_filters(movies, {"year": {"between": 3}})


def test_non_numeric_value_for_numeric_column_raises(movies):
    with pytest.raises(ValueError, match="Expected a number"):
        apply_filters(movies, {"year": {"gt": "abc"}})
