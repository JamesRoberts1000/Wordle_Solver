from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import requests


WORDLE_ARCHIVE_URL = (
    "https://raw.githubusercontent.com/Hamster45105/wordle-archive/main/solutions/wordle_solutions.json"
)


@dataclass(frozen=True)
class SolverInputs:
    include_letters: str
    exclude_letters: str
    known_positions: list[Optional[str]]
    disallowed_positions: list[str]


def normalize_letters(value: str, dedupe: bool = False) -> str:
    cleaned = "".join(ch for ch in value.lower().strip() if ch.isalpha())
    if not dedupe:
        return cleaned
    return "".join(dict.fromkeys(cleaned))


def normalize_positions(values: Iterable[str]) -> list[Optional[str]]:
    normalized: list[Optional[str]] = []
    for value in values:
        char = normalize_letters(value, dedupe=False)
        normalized.append(char[0] if char else None)
    return normalized[:5]


def normalize_disallowed_positions(values: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        normalized.append(normalize_letters(value, dedupe=True))
    while len(normalized) < 5:
        normalized.append("")
    return normalized[:5]


def load_word_frequency_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required_columns = {"word", "count"}
    if not required_columns.issubset(df.columns):
        raise ValueError("Dataset must include 'word' and 'count' columns.")

    df = df.copy()
    df["word"] = df["word"].astype(str).str.lower()
    df = df[df["word"].str.len() == 5]
    df = df.sort_values(by="count", ascending=False)
    df["rank"] = df["count"].rank(method="min", ascending=False).astype(int)
    return df.reset_index(drop=True)


def fetch_previous_solutions(
    url: str = WORDLE_ARCHIVE_URL,
    cutoff_days: int = 1,
    timeout_seconds: int = 10,
) -> pd.DataFrame:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    json_data = response.json()
    df = pd.DataFrame(list(json_data.items()), columns=["date", "word"])
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["word"] = df["word"].astype(str).str.lower()
    cutoff_date = pd.Timestamp.today() - timedelta(days=cutoff_days)
    return df[df["date"] < cutoff_date].reset_index(drop=True)


def _word_matches(
    word: str,
    include_letters: str,
    exclude_letters: str,
    known_positions: list[Optional[str]],
    disallowed_positions: list[str],
) -> bool:
    include_counts = Counter(include_letters)
    for letter, count in include_counts.items():
        if word.count(letter) < count:
            return False

    if exclude_letters and any(letter in word for letter in set(exclude_letters)):
        return False

    for idx, letter in enumerate(known_positions):
        if letter and word[idx] != letter:
            return False

    for idx, blocked_letters in enumerate(disallowed_positions):
        for letter in blocked_letters:
            # Wordle yellow logic: letter exists, but not in this index.
            if letter not in word or word[idx] == letter:
                return False

    return True


def filter_candidates(
    words_df: pd.DataFrame,
    inputs: SolverInputs,
) -> pd.DataFrame:
    filtered = words_df[
        words_df["word"].apply(
            lambda w: _word_matches(
                w,
                include_letters=inputs.include_letters,
                exclude_letters=inputs.exclude_letters,
                known_positions=inputs.known_positions,
                disallowed_positions=inputs.disallowed_positions,
            )
        )
    ]
    return filtered.reset_index(drop=True)


def score_candidates(candidates_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df.empty:
        return candidates_df.copy()

    scored = candidates_df.copy()
    max_log_count = np.log1p(scored["count"]).max()
    frequency_score = np.log1p(scored["count"]) / max_log_count if max_log_count > 0 else 0.0

    letter_weights = Counter()
    weighted_total = float(scored["count"].sum())
    for word, count in zip(scored["word"], scored["count"]):
        for letter in set(word):
            letter_weights[letter] += float(count)

    if weighted_total == 0:
        letter_prob = {letter: 0.0 for letter in letter_weights}
    else:
        letter_prob = {letter: weight / weighted_total for letter, weight in letter_weights.items()}

    coverage_score = scored["word"].apply(
        lambda word: float(sum(letter_prob.get(letter, 0.0) for letter in set(word)))
    )
    unique_bonus = scored["word"].apply(lambda word: len(set(word)) / 5.0)
    total_score = (0.6 * coverage_score) + (0.3 * frequency_score) + (0.1 * unique_bonus)

    scored["coverage_score"] = coverage_score.round(4)
    scored["frequency_score"] = np.round(frequency_score, 4)
    scored["unique_letter_bonus"] = unique_bonus.round(4)
    scored["total_score"] = total_score.round(4)
    scored = scored.sort_values(by=["total_score", "rank"], ascending=[False, True]).reset_index(drop=True)
    return scored


def add_previous_solution_flag(candidates_df: pd.DataFrame, previous_solutions_df: pd.DataFrame) -> pd.DataFrame:
    flagged = candidates_df.copy()
    previous_words = set(previous_solutions_df["word"]) if not previous_solutions_df.empty else set()
    flagged["seen_before"] = flagged["word"].isin(previous_words)
    return flagged
