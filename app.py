"""Project Hail Mary — Movie Analysis Dashboard.

Streamlit app for interactive visualization of subtitle analysis.

Usage:
    uv run streamlit run app.py
"""

import json
from pathlib import Path

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ── Config ──────────────────────────────────────────────────────────────────

CACHE_DIR = Path("data/cache")

EMOTION_COLORS = {
    "hope": "#FFD700",
    "despair": "#8B0000",
    "fear": "#FF4500",
    "wonder": "#9370DB",
    "determination": "#4169E1",
    "humor": "#32CD32",
    "grief": "#808080",
    "relief": "#20B2AA",
    "neutral": "#A9A9A9",
}

THEME_COLORS = {
    "Isolation/Survival": "#FF6B6B",
    "First Contact": "#4ECDC4",
    "Friendship/Trust": "#FFE66D",
    "Sacrifice": "#FF8E72",
    "Science/Curiosity": "#6C5CE7",
    "Hope/Despair": "#74B9FF",
}


# ── Data Loading ────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    """Load all JSON artifacts from cache directory."""
    def _load(name):
        path = CACHE_DIR / f"{name}.json"
        if not path.exists():
            st.error(f"Missing data file: {path}. Run `make process` first.")
            st.stop()
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    return {
        "subtitles": _load("subtitles"),
        "scenes": _load("scenes"),
        "characters": _load("characters"),
        "sentiment": _load("sentiment"),
        "emotional_arc": _load("emotional_arc"),
        "themes": _load("themes"),
        "dialogue_patterns": _load("dialogue_patterns"),
        "movie_barcode": _load("movie_barcode"),
    }


def fmt_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}:{m:02d}:{s:02d}"


# ── App ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Project Hail Mary — Analysis",
    page_icon="🚀",
    layout="wide",
)

data = load_data()
subtitles = data["subtitles"]
scenes = data["scenes"]
characters = data["characters"]
sentiment = data["sentiment"]
emotional_arc = data["emotional_arc"]
themes = data["themes"]
dialogue = data["dialogue_patterns"]
barcode = data["movie_barcode"]

total_duration = barcode["total_duration_sec"]

# ── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.title("🚀 Navigation")
section = st.sidebar.radio(
    "Jump to",
    ["Overview", "Emotional Arc", "Characters", "Interaction Heatmap",
     "Theme Timeline", "Dialogue Patterns", "Movie Barcode", "Scene Explorer"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Duration:** {fmt_time(total_duration)}")
st.sidebar.markdown(f"**Scenes:** {len(scenes)}")
st.sidebar.markdown(f"**Subtitles:** {len(subtitles)}")
top_chars = [c for c in characters if c["name"] != "unknown"][:5]
if top_chars:
    st.sidebar.markdown("**Top Speakers:**")
    for c in top_chars:
        st.sidebar.markdown(f"  {c['name']}: {c['lines']} lines")

# ── Overview ─────────────────────────────────────────────────────────────────

if section == "Overview":
    st.title("🚀 Project Hail Mary — Movie Analysis")

    st.markdown("An interactive exploration of dialogue, emotion, and theme in "
                "Project Hail Mary, based on subtitle analysis.")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    speaking_chars = [c for c in characters if c["name"] != "unknown"]
    dominant_mood = max(set(e["dominant_emotion"] for e in emotional_arc),
                       key=lambda x: sum(1 for e in emotional_arc if e["dominant_emotion"] == x))

    col1.metric("Duration", fmt_time(total_duration))
    col2.metric("Scenes", len(scenes))
    col3.metric("Characters", len(speaking_chars))
    col4.metric("Dominant Mood", dominant_mood.title())

    st.markdown("---")

    # Quick summary chart: sentiment over time
    arc_df_data = {
        "Time": [fmt_time(e["start"]) for e in emotional_arc],
        "Compound": [e["smoothed_compound"] for e in emotional_arc],
        "Emotion": [e["dominant_emotion"] for e in emotional_arc],
        "Scene": [e["label"] for e in emotional_arc],
    }
    fig = px.line(arc_df_data, x="Time", y="Compound", color="Emotion",
                  color_discrete_map=EMOTION_COLORS,
                  title="Emotional Arc — Smoothed Sentiment Over Time",
                  markers=True)
    fig.update_layout(
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e0e0e0", height=400,
        xaxis_title="Scene", yaxis_title="Sentiment Compound",
    )
    fig.update_traces(marker=dict(size=5))
    st.plotly_chart(fig, use_container_width=True)

    char_df = {
        "Character": [c["name"] for c in speaking_chars[:8]],
        "Words": [c["words"] for c in speaking_chars[:8]],
    }
    fig2 = px.bar(char_df, x="Character", y="Words",
                  title="Word Count by Character",
                  color="Character",
                  color_discrete_sequence=px.colors.qualitative.Set2)
        font_color="#e0e0e0", height=350,
        xaxis_title="Character", yaxis_title="Words",
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Emotional Arc ───────────────────────────────────────────────────────────

elif section == "Emotional Arc":
    st.title("💭 Emotional Arc")

    st.markdown("Sentiment and emotion tracked across scenes, smoothed with a 5-scene rolling window.")

    # Compound sentiment line
    arc_times = [e["start"] for e in emotional_arc]
    arc_labels = [e["label"] for e in emotional_arc]

    fig = go.Figure()

    # Smoothed compound
    fig.add_trace(go.Scatter(
        x=arc_times, y=[e["smoothed_compound"] for e in emotional_arc],
        mode="lines+markers", name="Smoothed Sentiment",
        line=dict(color="#c9a227", width=2),
        marker=dict(size=5, color=[EMOTION_COLORS.get(e["dominant_emotion"], "#A9A9A9") for e in emotional_arc]),
        customdata=[(e["label"], e["dominant_emotion"]) for e in emotional_arc],
        hovertemplate="<b>%{customdata[0]}</b><br>Emotion: %{customdata[1]}<br>Score: %{y:.3f}<extra></extra>",
    ))

    # Raw compound (lighter)
    fig.add_trace(go.Scatter(
        x=arc_times, y=[e["avg_compound"] for e in emotional_arc],
        mode="lines", name="Raw Sentiment",
        line=dict(color="#4a9eff", width=1, dash="dot"),
        opacity=0.5,
    ))

    fig.update_layout(
        title="Emotional Arc — Sentiment Over Time",
        xaxis_title="Time (seconds)", yaxis_title="Sentiment Compound",
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e0e0e0", height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_xaxes(tickformat="%M:%S", tick0=0, dtick=600)
    st.plotly_chart(fig, use_container_width=True)

    # Emotion distribution
    emotion_df = {
        "Emotion": list(emotion_counts.keys()),
        "Count": list(emotion_counts.values()),
    }
    fig2 = px.pie(
        emotion_df, names="Emotion", values="Count",
        color="Emotion",
        color_discrete_map=EMOTION_COLORS,
        title="Emotion Distribution Across Scenes",
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Characters ──────────────────────────────────────────────────────────────

elif section == "Characters":
    st.title("👥 Characters")

    speaking_chars = [c for c in characters if c["name"] != "unknown"]

    # Overview metrics
    col1, col2, col3 = st.columns(3)
    total_words = sum(c["words"] for c in speaking_chars)
    total_lines = sum(c["lines"] for c in speaking_chars)
    col1.metric("Speaking Characters", len(speaking_chars))
    col2.metric("Total Lines", total_lines)
    col3.metric("Total Words", total_words)

    st.markdown("---")

    # Character cards
    for c in speaking_chars[:10]:
        with st.expander(f"**{c['name']}** — {c['lines']} lines, {c['words']} words"):
            cols = st.columns(4)
            cols[0].metric("Lines", c["lines"])
            cols[1].metric("Words", c["words"])
            cols[2].metric("Speaking Time", fmt_time(c["total_speaking_time"]))
            cols[3].metric("Avg Words/Line", c["avg_line_length"])

            # Timeline bar
            total = total_duration if total_duration > 0 else 1
            start_pct = c["first_appearance"] / total * 100
            span_pct = c["screen_presence"] / total * 100
            st.markdown(
                f'<div style="background:#1a1a2e;height:24px;border-radius:4px;position:relative;">'
                f'<div style="background:#c9a227;height:24px;border-radius:4px;position:absolute;'
                f'left:{start_pct}%;width:{span_pct}%;"></div></div>'
                f'<small>Presence: {fmt_time(c["first_appearance"])} → {fmt_time(c["last_appearance"])} '
                f'({c["screen_presence"]:.0f}s)</small>',
                unsafe_allow_html=True,
            )

            # Interactions
            if c["interactions"]:
                st.markdown("**Talks after:**")
                for other, count in sorted(c["interactions"].items(), key=lambda x: -x[1])[:5]:
                    st.markdown(f"  → {other}: {count} times")

# ── Interaction Heatmap ─────────────────────────────────────────────────────

elif section == "Interaction Heatmap":
    st.title("🔥 Interaction Heatmap")

    st.markdown("Who talks after whom — character conversation flow matrix.")

    speaking_chars = [c for c in characters if c["name"] != "unknown"]
    char_names = [c["name"] for c in speaking_chars[:12]]  # Top 12

    # Build interaction matrix
    matrix = np.zeros((len(char_names), len(char_names)))
    for c in speaking_chars[:12]:
        if c["name"] in char_names and c["interactions"]:
            for other, count in c["interactions"].items():
                if other in char_names:
                    i = char_names.index(c["name"])
                    j = char_names.index(other)
                    matrix[i][j] += count

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=char_names,
        y=char_names,
        colorscale="YlOrRd",
        text=matrix.astype(int),
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate="%{y} → %{x}: %{z:int} transitions<extra></extra>",
    ))
    fig.update_layout(
        title="Character Interaction Matrix (Row talks after Column)",
        xaxis_title="Next Speaker", yaxis_title="Previous Speaker",
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e0e0e0", height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Theme Timeline ──────────────────────────────────────────────────────────

elif section == "Theme Timeline":
    st.title("🔍 Theme Timeline")

    st.markdown("Thematic intensity across the movie, based on keyword matching per scene.")

    scene_themes = themes["scene_themes"]
    theme_arcs = themes["theme_arcs"]

    # Stacked area chart
    fig = go.Figure()
    for theme, color in THEME_COLORS.items():
        arc_data = theme_arcs[theme]
        fig.add_trace(go.Scatter(
            x=[a["start"] for a in arc_data],
            y=[a["score"] for a in arc_data],
            name=theme,
            mode="lines",
            stackgroup="themes",
            line=dict(color=color, width=1.5),
            fillcolor=color,
            hovertemplate=f"<b>{theme}</b><br>Score: %{{y:.2f}}<extra></extra>",
        ))

    fig.update_layout(
        title="Theme Intensity Over Time",
        xaxis_title="Time (seconds)", yaxis_title="Keyword Hit Rate (%)",
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e0e0e0", height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_xaxes(tickformat="%M:%S", tick0=0, dtick=600)
    st.plotly_chart(fig, use_container_width=True)

    theme_df = {
        "Theme": list(dom_counts.keys()),
        "Count": list(dom_counts.values()),
    }
    fig2 = px.pie(
        theme_df, names="Theme", values="Count",
        color="Theme",
        color_discrete_map=THEME_COLORS,
        title="Dominant Theme Distribution",
    )
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e0e0e0", height=400,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Dialogue Patterns ───────────────────────────────────────────────────────

elif section == "Dialogue Patterns":
    st.title("💬 Dialogue Patterns")

    pat_counts = dialogue["pattern_counts"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Monologue Scenes", pat_counts.get("monologue", 0))
    col2.metric("Dialogue Scenes", pat_counts.get("dialogue", 0))
    col3.metric("Narration Scenes", pat_counts.get("narration", 0))

    pattern_df = {
        "Pattern": list(pat_counts.keys()),
        "Count": list(pat_counts.values()),
    }
    fig = px.pie(
        pattern_df, names="Pattern", values="Count",
        color="Pattern",
        color_discrete_map={"monologue": "#c9a227", "dialogue": "#4a9eff", "narration": "#A9A9A9"},
        title="Scene Pattern Distribution",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Conversations table
    st.subheader("Top Conversations")
    convs = dialogue["conversations"][:20]
    conv_data = []
    for c in convs:
        conv_data.append({
            "Turns": c["turns"],
            "Speakers": " ↔ ".join(c["speakers"]),
            "Avg Gap (s)": c["avg_gap_sec"],
            "Dominance": " / ".join(f"{k}:{v}" for k, v in sorted(c["dominance"].items(), key=lambda x: -x[1])),
        })
    st.dataframe(conv_data, use_container_width=True)

    # Per-scene pattern timeline
    sp_data = dialogue["scene_patterns"]
    sp_df = {
        "Time": [s["start"] for s in sp_data],
        "PatternValue": [1 if s["pattern"] == "dialogue" else (0 if s["pattern"] == "monologue" else -1) for s in sp_data],
        "Pattern": [s["pattern"] for s in sp_data],
    }
    fig2 = px.scatter(
        sp_df, x="Time", y="PatternValue", color="Pattern",
        color_discrete_map={"monologue": "#c9a227", "dialogue": "#4a9eff", "narration": "#A9A9A9"},
        title="Dialogue Pattern Over Time",
        labels={"Time": "Time (seconds)", "PatternValue": "Pattern"},
    )
    fig2.update_layout(
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e0e0e0", height=300,
        yaxis=dict(tickmode="array", tickvals=[-1, 0, 1],
                   ticktext=["Narration", "Monologue", "Dialogue"]),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Movie Barcode ───────────────────────────────────────────────────────────

elif section == "Movie Barcode":
    st.title("🎞️ Movie Barcode")

    st.markdown("Dialogue intensity over time — each column represents a 10-second window.")

    bc = barcode["barcode"]
    times = [b["start"] for b in bc]
    words = [b["words"] for b in bc]
    subs = [b["subtitle_count"] for b in bc]

    # Create barcode as a horizontal heatmap
    fig = go.Figure()

    # Word density barcode
    fig.add_trace(go.Heatmap(
        z=[words],
        colorscale=[[0, "#0a0a0f"], [0.3, "#1a1a2e"], [0.6, "#c9a227"], [1, "#ff6b6b"]],
        showscale=True,
        colorbar=dict(title="Words/10s"),
        hovertemplate="Time: %{x}s<br>Words: %{z}<extra></extra>",
    ))

    fig.update_layout(
        title="Dialogue Intensity Barcode",
        xaxis_title="Time (seconds)",
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e0e0e0", height=200,
        yaxis=dict(showticklabels=False),
    )
    fig.update_xaxes(tick0=0, dtick=600)
    st.plotly_chart(fig, use_container_width=True)
    wpm_data = {
        "Time": times,
        "WPM": [w * 6 for w in words],
    }
    fig2 = px.area(
        wpm_data, x="Time", y="WPM",
        title="Dialogue Pace (Words per Minute)",
        labels={"Time": "Time (seconds)", "WPM": "Words/min"},
    )
    fig2.update_xaxes(tickformat="%M:%S", tick0=0, dtick=600)
    st.plotly_chart(fig2, use_container_width=True)

# ── Scene Explorer ──────────────────────────────────────────────────────────

elif section == "Scene Explorer":
    st.title("🎬 Scene Explorer")

    # Filters
    col1, col2, col3 = st.columns(3)

    # Character filter
    speaking_chars = [c["name"] for c in characters if c["name"] != "unknown"]
    selected_chars = col1.multiselect("Filter by Character", speaking_chars, default=[])

    # Emotion filter
    all_emotions = list(set(e["dominant_emotion"] for e in emotional_arc))
    selected_emotions = col2.multiselect("Filter by Emotion", all_emotions, default=[])

    # Pattern filter
    all_patterns = list(dialogue["pattern_counts"].keys())
    selected_patterns = col3.multiselect("Filter by Pattern", all_patterns, default=[])

    # Build scene display data
    sub_map = {s["id"]: s for s in subtitles}
    scene_data = []
    for scene, arc, sp in zip(scenes, emotional_arc, dialogue["scene_patterns"]):
        # Apply filters
        if selected_chars:
            scene_subs = [sub_map[sid] for sid in scene["subtitle_ids"] if sid in sub_map]
            scene_speakers = {s["speaker"] for s in scene_subs if s["speaker"]}
            if not scene_speakers.intersection(selected_chars):
                continue
        if selected_emotions and arc["dominant_emotion"] not in selected_emotions:
            continue
        if selected_patterns and sp["pattern"] not in selected_patterns:
            continue

        scene_data.append({
            "ID": scene["id"],
            "Time": f"{fmt_time(scene['start'])} - {fmt_time(scene['end'])}",
            "Duration": f"{scene['duration_sec']:.0f}s",
            "Label": scene["label"][:60],
            "Emotion": arc["dominant_emotion"],
            "Pattern": sp["pattern"],
            "Words": sp["total_words"],
            "Lines": sp["total_lines"],
        })

    st.markdown(f"**Showing {len(scene_data)} of {len(scenes)} scenes**")
    st.dataframe(scene_data, use_container_width=True)

    # Selected scene detail
    st.markdown("---")
    scene_id = st.selectbox("View scene detail", range(1, len(scenes) + 1),
                            format_func=lambda i: f"Scene {i}: {scenes[i-1]['label'][:40]}")

    scene = scenes[scene_id - 1]
    arc = emotional_arc[scene_id - 1]
    sp = dialogue["scene_patterns"][scene_id - 1]

    st.markdown(f"### Scene {scene['id']}: {scene['label']}")
    cols = st.columns(4)
    cols[0].metric("Duration", f"{scene['duration_sec']:.0f}s")
    cols[1].metric("Emotion", arc["dominant_emotion"].title())
    cols[2].metric("Pattern", sp["pattern"].title())
    cols[3].metric("Sentiment", f"{arc['avg_compound']:.3f}")

    # Scene subtitle text
    st.subheader("Dialogue")
    scene_subs = [sub_map[sid] for sid in scene["subtitle_ids"] if sid in sub_map]
    dialogue_text = []
    for sub in scene_subs:
        speaker = sub["speaker"] or "—"
        text = sub["text"] or sub["raw_text"]
        sentiment = sub.get("sentiment", {}).get("compound", 0)
        sentiment_icon = "😊" if sentiment > 0.3 else "😟" if sentiment < -0.3 else "😐"
        dialogue_text.append(f"**{speaker}** {sentiment_icon}  {text}")

    st.markdown("\n".join(dialogue_text[:30]))