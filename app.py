import pandas as pd
import streamlit as st

from solver import (
    SolverInputs,
    add_previous_solution_flag,
    fetch_previous_solutions,
    filter_candidates,
    load_word_frequency_dataset,
    normalize_disallowed_positions,
    normalize_letters,
    normalize_positions,
    score_candidates,
)


st.set_page_config(page_title="Wordle Solver", page_icon="🟩", layout="wide")
st.title("Wordle Solver")
st.caption("Portfolio project: rule-based filtering + transparent recommendation scoring.")

st.markdown(
    """
Use the controls to narrow the candidate list:
- **Exclude letters**: gray letters not present in the answer.
- **Include letters**: yellow/green letters that must be present.
- **Known positions**: letters confirmed at each position.
- **Not in this position**: yellow letters known to be wrong at that index.
"""
)

if st.button("Reset inputs"):
    for key in [
        "letters_to_exclude",
        "letters_to_include",
        "letters_in_position1",
        "letters_in_position2",
        "letters_in_position3",
        "letters_in_position4",
        "letters_in_position5",
        "letters_not_in_position1",
        "letters_not_in_position2",
        "letters_not_in_position3",
        "letters_not_in_position4",
        "letters_not_in_position5",
    ]:
        st.session_state[key] = ""
    st.rerun()

letters_to_exclude_raw = st.text_input("Letters to exclude", key="letters_to_exclude")
letters_to_include_raw = st.text_input("Letters to include", key="letters_to_include")

st.write("Known positions")
col1, col2, col3, col4, col5 = st.columns(5)
position_values_raw = [
    col1.text_input("1", max_chars=1, key="letters_in_position1"),
    col2.text_input("2", max_chars=1, key="letters_in_position2"),
    col3.text_input("3", max_chars=1, key="letters_in_position3"),
    col4.text_input("4", max_chars=1, key="letters_in_position4"),
    col5.text_input("5", max_chars=1, key="letters_in_position5"),
]

st.write("Letters in word but not in this position (yellow)")
yellow_col1, yellow_col2, yellow_col3, yellow_col4, yellow_col5 = st.columns(5)
disallowed_position_values_raw = [
    yellow_col1.text_input("Not in 1", key="letters_not_in_position1"),
    yellow_col2.text_input("Not in 2", key="letters_not_in_position2"),
    yellow_col3.text_input("Not in 3", key="letters_not_in_position3"),
    yellow_col4.text_input("Not in 4", key="letters_not_in_position4"),
    yellow_col5.text_input("Not in 5", key="letters_not_in_position5"),
]
st.caption("Example: if 'a' is yellow in position 2, type `a` in `Not in 2`.")

inputs = SolverInputs(
    include_letters=normalize_letters(letters_to_include_raw, dedupe=False),
    exclude_letters=normalize_letters(letters_to_exclude_raw, dedupe=True),
    known_positions=normalize_positions(position_values_raw),
    disallowed_positions=normalize_disallowed_positions(disallowed_position_values_raw),
)

try:
    words_df = load_word_frequency_dataset("unigram_freq.csv")
except Exception as exc:
    st.error(f"Failed to load unigram dataset: {exc}")
    st.stop()

try:
    previous_solutions_df = fetch_previous_solutions()
except Exception as exc:
    previous_solutions_df = pd.DataFrame(columns=["word", "date"])
    st.warning(f"Wordle archive unavailable; running without history filter. Details: {exc}")

candidates = filter_candidates(words_df, inputs)
scored = score_candidates(candidates)
flagged = add_previous_solution_flag(scored, previous_solutions_df)

if flagged.empty:
    st.warning("No words match your current constraints.")
    st.stop()

st.subheader("Top 10 next guesses")
st.dataframe(
    flagged.loc[
        :, ["word", "rank", "total_score", "coverage_score", "frequency_score", "unique_letter_bonus", "seen_before"]
    ].head(10),
    use_container_width=True,
    hide_index=True,
)

st.subheader("All matching candidates")
st.dataframe(
    flagged.loc[
        :, ["word", "rank", "total_score", "coverage_score", "frequency_score", "unique_letter_bonus", "seen_before"]
    ],
    use_container_width=True,
    hide_index=True,
)

seen_before_words = flagged[flagged["seen_before"]]["word"].tolist()
if seen_before_words:
    st.info(f"Matches that already appeared in historical Wordle answers: {', '.join(seen_before_words[:20])}")
else:
    st.success("No matches found in the historical Wordle archive.")
