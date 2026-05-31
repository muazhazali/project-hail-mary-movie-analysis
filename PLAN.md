# Project Hail Mary — Movie Analysis Dashboard

## Implementation Plan

### What We Have

- **SRT subtitle file** (~2,000 entries, ~104 min runtime, HI captions with speaker labels like `[RYLAND]`, `[ROCKY]`, sound effects in brackets)
- **MP4 video file** (2.9 GB, IMAX 1080p)
- **Empty `data/cache/`** directory for processed artifacts
- **No existing code** — starting from scratch

### What We're Building

A self-contained **Python + Streamlit** analysis pipeline + interactive dashboard that extracts deep insights from the subtitle data and presents them visually. No LLM API calls at runtime — all analysis is done in preprocessing, dashboard is a Streamlit app.

---

## Architecture

```
project-hail-mary-movie-analysis/
├── .env                              # API keys (for optional LLM enrichment)
├── .gitignore
├── .python-version                   # Python version pin (e.g., 3.12)
├── pyproject.toml                    # uv project config + deps
├── uv.lock                           # Lock file (auto-generated)
├── Makefile                          # Orchestrate: process → serve
├── analyze.py                        # Main pipeline: SRT → JSON artifacts
├── app.py                            # Streamlit dashboard app
├── data/
│   ├── Project.Hail.Mary...srt       # Source subtitle
│   ├── Project.Hail.Mary...mp4       # Source video (large, not processed)
│   └── cache/                        # Generated JSON artifacts
│       ├── subtitles.json            # Raw parsed subtitles
│       ├── scenes.json               # Scene-by-scene breakdown
│       ├── characters.json           # Character profiles + stats
│       ├── sentiment.json            # Per-subtitle sentiment scores
│       ├── themes.json               # Extracted themes + per-scene scores
│       ├── dialogue_patterns.json    # Conversation dynamics
│       ├── emotional_arc.json        # Smoothed emotional timeline
│       └── movie_barcode.json        # Dialogue intensity barcode data
└── README.md                         # (only if explicitly requested)
```

### Python Environment

Use **uv** for fast, reproducible virtual environment management:

```bash
# Create venv and install deps
uv venv
uv pip install -r pyproject.toml

# Or using uv run (no activate needed)
uv run python analyze.py
uv run streamlit run app.py
```

---

## Phase 1: SRT Parser & Data Extraction

**Goal**: Parse the SRT into structured Python objects.

### What to build

1. **SRT parser** — Read `.srt`, handle HI (hearing-impaired) markers:
   - Strip sound effect annotations (`[thunder rumbles]`, `[music playing]`)
   - Extract speaker tags (`[RYLAND]`, `[ROCKY]`) as character identifiers
   - Handle multi-line entries, HTML italic tags
2. **Time normalization** — Convert `HH:MM:SS,mmm` timestamps to seconds
3. **Subtitle model** — Each entry: `{id, start_sec, end_sec, speaker, text, raw_text}`

### Output

- `data/cache/subtitles.json`

### Key decisions

- HI tags in `[brackets]` → separate into `speaker` vs `sfx` fields
- Lines without speaker tags → infer from context or mark as `narrator/unknown`

---

## Phase 2: Scene Segmentation

**Goal**: Break the ~104-minute subtitle stream into logical scenes.

### Algorithm

1. **Gap-based segmentation**: Gaps > 3 seconds between subtitle entries → scene boundary
2. **Merge tiny scenes**: Scenes < 15 seconds → merge with adjacent
3. **Label scenes**: Use dominant speaker + key dialogue to generate short labels

### Output

- `data/cache/scenes.json` — Array of `{id, start, end, label, subtitle_ids, duration_sec}`

### Expected result

- ~40–60 scenes for a 104-minute movie

---

## Phase 3: Character Analysis

**Goal**: Build profiles for each speaking character.

### What to extract

1. **Speaker identification** — Group all subtitles by speaker tag
2. **Dialogue stats per character**:
   - Total lines, total words, total speaking time
   - Average line length (words per line)
   - First appearance, last appearance, screen presence span
3. **Character interaction matrix** — Who talks after whom (conversation flow)
4. **Solo vs dialogue ratio** — % of lines spoken alone vs in conversation

### Output

- `data/cache/characters.json`

### Key characters expected

- Ryland Grace (protagonist)
- Rocky (alien companion)
- Possibly: Stratt, other crew, voices

---

## Phase 4: Sentiment & Emotional Analysis

**Goal**: Score each subtitle/scene for emotional tone.

### Approach (no LLM at runtime)

1. **VADER sentiment** — Rule-based, fast, no API needed. `vaderSentiment`
2. **Per-subtitle sentiment** — Score each line
3. **Per-scene aggregation** — Average sentiment across scene's subtitles, weighted by line length
4. **Smoothing** — Rolling window (5-scene) for emotional arc curve
5. **Emotion classification** — Map compound sentiment + keyword heuristics to categories:
   - Categories: `[despair, fear, hope, wonder, determination, humor, grief, relief]`
   - Keyword lists: e.g., "die/death/killed" → fear/grief, "light/star/sun" → hope

### Output

- `data/cache/sentiment.json` — Per-subtitle scores
- `data/cache/emotional_arc.json` — Smoothed per-scene emotional timeline

---

## Phase 5: Theme Extraction

**Goal**: Identify recurring thematic threads.

### Approach

1. **Keyword frequency analysis** — TF-IDF on per-scene text corpora
2. **Thematic clusters** — Predefined theme buckets mapped to keyword sets:

| Theme | Keywords |
|-------|----------|
| Isolation/Survival | alone, survive, die, death, last, only, stranded |
| First Contact | alien, species, communicate, language, signal |
| Friendship/Trust | friend, trust, together, help, partner, believe |
| Sacrifice | sacrifice, give, risk, save, worth, mission |
| Science/Curiosity | experiment, data, calculate, theory, evidence, test |
| Hope/Despair | hope, impossible, miracle, chance, never, lost |

3. **Per-scene theme scores** — Percentage of theme-keyword hits per scene
4. **Theme arc** — How each theme rises/falls over the movie

### Output

- `data/cache/themes.json` — Theme definitions + per-scene scores + dominant themes

---

## Phase 6: Dialogue Pattern Analysis

**Goal**: Detect conversation dynamics — who dominates, rapid exchanges vs monologues.

### What to extract

1. **Conversation detection** — Group subtitles where same speakers alternate within 5-second gaps
2. **Pattern classification per scene**:
   - **Monologue**: One speaker, >70% of words in a span
   - **Dialogue**: Rapid back-and-forth (avg < 3 sec between speakers)
   - **Narration**: No speaker tag, descriptive text
3. **Turn-taking metrics**:
   - Average turns per conversation
   - Speaker dominance ratio (e.g., Ryland 60% / Rocky 40%)
   - Interruption detection (speaker change before previous line ends)
4. **Dialogue intensity timeline** — Words-per-minute rolling average → "movie barcode"

### Output

- `data/cache/dialogue_patterns.json` — Per-scene pattern classification + metrics
- `data/cache/movie_barcode.json` — Words-per-second for every 10-second window → barcode visualization

---

## Phase 7: Streamlit Dashboard

**Goal**: Beautiful, cinematic interactive dashboard powered by Streamlit.

### Tech

- **Streamlit** — Python web framework for data apps, no HTML/CSS/JS needed
- **Plotly** — Interactive charts (via Streamlit native integration)
- **Dark cinematic theme** — Custom Streamlit theming via `.streamlit/config.toml`

### Dashboard sections

1. **Hero header** — Movie title, runtime, # scenes, # characters, dominant mood (via `st.columns` + `st.metric`)
2. **Emotional Arc chart** — Plotly line chart (x: time, y: sentiment compound) with scene hover
3. **Character spotlight** — Expandable cards for each character with stat bars (`st.expander` + `st.progress` / Plotly bar charts)
4. **Interaction heatmap** — Plotly heatmap of who talks to whom
5. **Theme timeline** — Plotly stacked area chart showing theme intensity over time
6. **Dialogue pattern breakdown** — Pie chart (monologue vs dialogue vs narration) + per-scene view
7. **Movie barcode** — Plotly heatmap strip showing dialogue intensity over time
8. **Scene explorer** — `st.dataframe` or `st.data_editor` with filters by theme/character/mood

### Visual design principles

- Dark background (`#0a0a0f`), gold accent (`#c9a227`), cool blue secondary (`#4a9eff`)
- Typography: Streamlit defaults with custom font override if desired
- Sidebar navigation (`st.sidebar`) for section links
- Responsive by default (Streamlit handles mobile)

### Streamlit config

`.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#c9a227"
backgroundColor = "#0a0a0f"
secondaryBackgroundColor = "#1a1a2e"
textColor = "#e0e0e0"
font = "sans serif"

[server]
maxUploadSize = 50
```

---

## Phase 8: Optional LLM Enrichment

**Goal**: Use an LLM API (OpenAI/Anthropic via `.env`) to add richer metadata.

### What it adds (optional, not required for dashboard to work)

- Scene summaries (natural language)
- Character relationship descriptions
- Deeper theme interpretation
- Emotional nuance beyond VADER

### How

- `analyze.py --enrich` flag triggers LLM calls per scene
- Results cached in `data/cache/enriched.json`
- Dashboard merges enriched data if present, falls back gracefully if not

---

## Execution Order

| Step | Phase | Key Files | Depends On |
|------|-------|-----------|------------|
| 1 | Project setup | `pyproject.toml`, `.python-version`, `Makefile` | — |
| 2 | SRT parser | `analyze.py` (parser section) | — |
| 3 | Scene segmentation | `analyze.py` (scenes section) | Step 2 |
| 4 | Character analysis | `analyze.py` (characters section) | Step 2 |
| 5 | Sentiment analysis | `analyze.py` (sentiment section) | Steps 2, 3 |
| 6 | Theme extraction | `analyze.py` (themes section) | Steps 2, 3 |
| 7 | Dialogue patterns | `analyze.py` (patterns section) | Steps 2, 3, 4 |
| 8 | Streamlit dashboard | `app.py`, `.streamlit/config.toml` | Steps 3–7 (JSON outputs) |
| 9 | Movie barcode | `app.py` (barcode section) | Step 7 |
| 10 | Integration test | Full pipeline run + serve | All |

---

## Dependencies

```toml
# pyproject.toml [project.dependencies]
dependencies = [
    "streamlit>=1.38",
    "plotly>=5.24",
    "vaderSentiment>=3.3",
    "numpy>=1.26",
]
```

No Node, no CDN, no build step. Streamlit + Plotly handle all visualization natively.

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Language | Python | Ecosystem for NLP, easy scripting |
| Python env | uv venv | Fast, reproducible, lockfile-based |
| Frontend framework | Streamlit | Rapid prototyping, native Python, interactive widgets, no JS needed |
| Charts | Plotly (via Streamlit) | Interactive, animated, dark-theme friendly, Python-native |
| Sentiment | VADER (rule-based) | No API needed, good on short texts, fast |
| Data format | JSON files | Simple, human-readable, no DB needed |
| Video processing | Skip for v1 | 2.9 GB video is heavy; subtitles carry the signal |
| LLM enrichment | Optional, behind flag | Keeps core pipeline offline-runnable |