# Project Hail Mary — Movie Analysis Dashboard

Interactive analysis of dialogue, emotion, and themes from the Project Hail Mary subtitle data, powered by Python + Streamlit.

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager

## Setup

```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -e .
```

## Run

### Step 1 — Generate data artifacts

```bash
uv run python analyze.py
```

This parses the SRT file and writes JSON to `data/cache/`:

| File | Content |
|------|---------|
| `subtitles.json` | Parsed subtitle entries with speaker tags |
| `scenes.json` | Scene segmentation with labels |
| `characters.json` | Character profiles and interaction matrices |
| `sentiment.json` | Per-subtitle VADER sentiment scores |
| `emotional_arc.json` | Per-scene smoothed emotional timeline |
| `themes.json` | Theme keyword scores per scene |
| `dialogue_patterns.json` | Monologue/dialogue/narration classification |
| `movie_barcode.json` | Dialogue intensity per 10-second window |

### Step 2 — Launch the dashboard

```bash
uv run streamlit run app.py
```

Opens in your browser at `http://localhost:8501`.

## Using Make

```bash
make process    # Run the analysis pipeline
make serve      # Launch Streamlit dashboard
make all        # Process then serve
make clean      # Remove cached JSON artifacts
```

## Dashboard Sections

| Section | Description |
|---------|-------------|
| Overview | Key metrics, sentiment arc, word counts |
| Emotional Arc | Smoothed sentiment + emotion distribution |
| Characters | Per-character stats, presence bars, interactions |
| Interaction Heatmap | Who-talks-after-whom matrix |
| Theme Timeline | Stacked area chart of theme intensity |
| Dialogue Patterns | Monologue/dialogue/narration breakdown |
| Movie Barcode | Dialogue density heatmap over time |
| Scene Explorer | Filterable scene table with detail view |

## Optional: LLM Enrichment

```bash
uv pip install -e ".[enrich]"
uv run python analyze.py --enrich
```

Requires `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env`. Adds scene summaries and deeper emotional nuance. The dashboard works without it.