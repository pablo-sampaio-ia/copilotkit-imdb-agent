from imdb import images
from imdb.python_sandbox import run_snippet
from imdb.summary import summarize


def test_summary_splits_genres(movies):
    text = summarize(movies, "genre", "rating", filters=None)
    assert "- Action: count=3" in text  # A, D e F
    assert "mean=7.33" in text


def test_summary_notes_missing_values(movies):
    text = summarize(movies, "year", "rating", filters=None)
    assert "1 of 6 rows have no rating_imdb" in text


def test_summary_empty_filter(movies):
    assert summarize(movies, "year", "rating", {"year": 1900}) == "No rows match the given filters."


def test_snippet_returns_printed_text_and_result(movies):
    out = run_snippet("print('hi')\nresult = int(df['vote'].sum())", movies)
    assert out["is_error"] is False
    assert out["image_id"] is None
    assert "hi" in out["text"] and "4760" in out["text"]


def test_snippet_error_is_reported_not_raised(movies):
    out = run_snippet("1/0", movies)
    assert out["is_error"] is True
    assert "ZeroDivisionError" in out["text"]


def test_snippet_has_no_imports(movies):
    assert run_snippet("import os", movies)["is_error"] is True


def test_snippet_figure_becomes_png(movies, tmp_path, monkeypatch):
    monkeypatch.setattr(images, "IMAGE_DIR", tmp_path)
    out = run_snippet("plt.bar(df['title'], df['vote'])", movies)
    assert out["is_error"] is False
    assert out["image_id"]
    path = images.image_path(out["image_id"])
    assert path is not None and path.read_bytes().startswith(b"\x89PNG")


def test_image_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(images, "IMAGE_DIR", tmp_path)
    assert images.image_path("../secret") is None
    assert images.image_path("0" * 32) is None
