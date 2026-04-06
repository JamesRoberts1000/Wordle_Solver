import pandas as pd
import pytest

from solver import (
    SolverInputs,
    add_previous_solution_flag,
    fetch_previous_solutions,
    filter_candidates,
    normalize_disallowed_positions,
    normalize_letters,
    normalize_positions,
    score_candidates,
)


@pytest.fixture
def sample_words_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "word": ["crane", "cigar", "array", "eerie", "slate", "trace"],
            "count": [100, 80, 50, 30, 90, 70],
            "rank": [1, 3, 5, 6, 2, 4],
        }
    )


def test_include_exclude_filtering(sample_words_df: pd.DataFrame) -> None:
    inputs = SolverInputs(
        include_letters="ra",
        exclude_letters="g",
        known_positions=[None] * 5,
        disallowed_positions=[""] * 5,
    )
    result = filter_candidates(sample_words_df, inputs)
    assert set(result["word"]) == {"crane", "array", "trace"}


def test_fixed_position_filtering(sample_words_df: pd.DataFrame) -> None:
    inputs = SolverInputs(
        include_letters="",
        exclude_letters="",
        known_positions=["c", None, None, None, "e"],
        disallowed_positions=[""] * 5,
    )
    result = filter_candidates(sample_words_df, inputs)
    assert list(result["word"]) == ["crane"]


def test_repeated_letter_requirement(sample_words_df: pd.DataFrame) -> None:
    inputs = SolverInputs(
        include_letters="rr",
        exclude_letters="",
        known_positions=[None] * 5,
        disallowed_positions=[""] * 5,
    )
    result = filter_candidates(sample_words_df, inputs)
    assert list(result["word"]) == ["array"]


def test_disallowed_position_filtering(sample_words_df: pd.DataFrame) -> None:
    inputs = SolverInputs(
        include_letters="c",
        exclude_letters="",
        known_positions=[None] * 5,
        disallowed_positions=["c", "", "", "", ""],
    )
    result = filter_candidates(sample_words_df, inputs)
    assert set(result["word"]) == {"trace"}


def test_previous_solution_flag(sample_words_df: pd.DataFrame) -> None:
    previous = pd.DataFrame({"word": ["trace", "cigar"]})
    flagged = add_previous_solution_flag(sample_words_df, previous)
    seen_map = dict(zip(flagged["word"], flagged["seen_before"]))
    assert seen_map["trace"] is True
    assert seen_map["crane"] is False


def test_scoring_adds_expected_columns(sample_words_df: pd.DataFrame) -> None:
    scored = score_candidates(sample_words_df)
    for col in ["coverage_score", "frequency_score", "unique_letter_bonus", "total_score"]:
        assert col in scored.columns
    assert scored["total_score"].is_monotonic_decreasing


def test_fetch_previous_solutions_failure_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_error(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("network down")

    monkeypatch.setattr("solver.requests.get", _raise_error)
    with pytest.raises(RuntimeError):
        fetch_previous_solutions()


def test_normalization_helpers() -> None:
    assert normalize_letters(" A a!B ", dedupe=True) == "ab"
    assert normalize_positions(["A", "", " c ", "12", "E"]) == ["a", None, "c", None, "e"]
    assert normalize_disallowed_positions([" Aa ", "", "bB", "", " c! "]) == ["a", "", "b", "", "c"]
