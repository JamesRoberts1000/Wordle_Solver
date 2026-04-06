# Wordle Solver

A Streamlit app that helps solve daily Wordle puzzles by combining:
- rule-based candidate filtering from game feedback, and
- transparent scoring to rank the next best guesses.

## Problem

Wordle gives limited feedback each turn. The goal is to narrow the solution space quickly and choose high-information guesses.

## Data Sources

- Local word-frequency corpus: `unigram_freq.csv`
- Historical Wordle answers archive:
  - https://raw.githubusercontent.com/Hamster45105/wordle-archive/main/solutions/wordle_solutions.json

## Method

1. Keep only 5-letter words.
2. Apply constraints:
   - include letters (yellow/green),
   - exclude letters (gray),
   - fixed letter positions (green).
3. Score remaining words using:
   - `coverage_score`: weighted sum of unique-letter prevalence among remaining candidates,
   - `frequency_score`: normalized log word frequency from corpus,
   - `unique_letter_bonus`: favors diverse-letter guesses.
4. Combine into:
   - `total_score = 0.6 * coverage + 0.3 * frequency + 0.1 * unique_bonus`

The app shows top recommendations with component-level score transparency.

## Project Structure

- `app.py` - Streamlit UI
- `solver.py` - data loading, filtering, and scoring logic
- `tests/test_solver.py` - unit tests for core solver behavior

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Validation

The test suite checks:
- include/exclude filters,
- fixed-position filtering,
- repeated-letter constraints,
- fallback behavior when Wordle history cannot be fetched.

Run:

```bash
pytest -q
```

## Assumptions and Limitations

- Uses unigram frequency as a proxy for guess quality; this is not full entropy optimization.
- Exclusion logic assumes excluded letters are globally absent (does not yet model nuanced repeated-letter feedback from Wordle).
- Historical archive fetch is network-dependent; app continues gracefully when unavailable.

## Portfolio Presentation Checklist

- Add a deployed app URL (Streamlit Community Cloud) below.
- Optionally include one short write-up comparing this heuristic vs entropy-based methods.

## Screenshots

![Empty state](screenshots/01-empty-state.png)
![Top guesses](screenshots/02-top-guesses.png)
![Fallback warning](screenshots/03-fallback-warning.png)

## Live Demo

- Add deployment link here after publishing:
  - `https://<your-streamlit-app-url>`

## Deploy To Streamlit Community Cloud (Step-by-Step)

1. Push this project to a public GitHub repository.
2. Go to [https://share.streamlit.io/](https://share.streamlit.io/) and sign in with GitHub.
3. Click **Create app**.
4. Select:
   - **Repository**: your Wordle repo
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `app.py`
5. Expand **Advanced settings** and confirm:
   - Python dependencies are read from `requirements.txt`.
6. Click **Deploy**.
7. After deployment completes:
   - copy the app URL,
   - paste it into the **Live Demo** section above,
   - add the same link to your GitHub repo description.

If deployment fails:
- open the app logs in Streamlit Cloud,
- verify `requirements.txt` installs cleanly,
- confirm `app.py` and `unigram_freq.csv` are in the repo root.

## Manual Validation Scenarios

Run these quick checks before sharing:

1. **Base run**
   - Launch app with no filters.
   - Expect non-empty candidate table and top-10 table.
2. **Include/exclude**
   - Include: `ra`, Exclude: `g`.
   - Expect words containing `r` and `a`, and no `g`.
3. **Known position**
   - Position 1 = `c`, Position 5 = `e`.
   - Expect results like `crane`-style pattern only.
4. **Repeated letters**
   - Include: `rr`.
   - Expect only words with at least two `r` letters.
5. **Fallback behavior**
   - Temporarily disable internet and reload app.
   - Expect warning about archive fetch, but app still returns candidates.

## What I Would Build Next

- Add full Wordle feedback modeling (green/yellow/gray by position and count).
- Implement entropy/information-gain ranking and compare against current heuristic.
- Add historical backtesting: average guesses needed across archived answers.
