"""Project Hail Mary — Movie Analysis Pipeline.

Processes SRT subtitle file into structured JSON artifacts for the Streamlit dashboard.

Usage:
    uv run python analyze.py            # Run full pipeline
    uv run python analyze.py --enrich   # Run pipeline + optional LLM enrichment
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ── Paths ──────────────────────────────────────────────────────────────────

SRT_PATH = Path("data/Project.Hail.Mary.2026.1080p.WEB-DL.DDP5.1.Atmos.H.264-RDNYB-HI.srt")
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SENTIMENT_ENGINE = SentimentIntensityAnalyzer()

# ── Theme keyword sets ──────────────────────────────────────────────────────

THEME_KEYWORDS: dict[str, list[str]] = {
    "Isolation/Survival": [
        "alone", "survive", "die", "death", "last", "only", "stranded",
        "alive", "live", "living", "dying", "help", "save", "rescue",
    ],
    "First Contact": [
        "alien", "species", "communicate", "communication", "language",
        "signal", "message", "understand", "translate", "creature",
    ],
    "Friendship/Trust": [
        "friend", "trust", "together", "partner", "believe", "believed",
        "loyal", "betray", "honest", "promise", "care", "love",
    ],
    "Sacrifice": [
        "sacrifice", "give", "risk", "save", "worth", "mission",
        "dangerous", "hero", "brave", "choice", "give up", "lose",
    ],
    "Science/Curiosity": [
        "experiment", "data", "calculate", "theory", "evidence", "test",
        "discovery", "science", "scientist", "research", "analysis",
        "hypothesis", "observation", "physics", "biology", "chemistry",
    ],
    "Hope/Despair": [
        "hope", "impossible", "miracle", "chance", "never", "lost",
        "maybe", "perhaps", "wish", "dream", "faith", "believe",
    ],
}

# Emotion keyword heuristics
EMOTION_KEYWORDS: dict[str, list[str]] = {
    "despair": ["die", "death", "lost", "gone", "over", "end", "never", "impossible", "hopeless", "fail"],
    "fear": ["afraid", "scared", "danger", "scary", "terrified", "horror", "monster", "kill", "killed", "attack"],
    "hope": ["hope", "maybe", "possible", "chance", "light", "star", "sun", "bright", "work", "solution"],
    "wonder": ["wow", "amazing", "incredible", "beautiful", "magnificent", "extraordinary", "incredible"],
    "determination": ["must", "will", "need", "going to", "have to", "can't give up", "fight", "try", "do it"],
    "humor": ["ha", "funny", "joke", "laugh", "ridiculous", "stupid", "crazy", "weird"],
    "grief": ["miss", "sorry", "lost", "gone", "remember", "memory", "sad", "cry", "tears"],
    "relief": ["safe", "okay", "fine", "good", "glad", "thank", "finally", "better", "alive"],
}


# ── Phase 1: SRT Parser ────────────────────────────────────────────────────

def parse_srt(path: Path) -> list[dict]:
    """Parse SRT file into structured subtitle records."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n\s*\n", content.strip())

    subtitles = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        try:
            seq = int(lines[0].strip())
        except ValueError:
            continue

        ts_match = re.match(
            r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
            lines[1].strip(),
        )
        if not ts_match:
            continue

        g = ts_match.groups()
        start_sec = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
        end_sec = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000

        raw_lines = lines[2:]
        raw_text = " ".join(raw_lines)

        speaker = None
        sfx_tags: list[str] = []
        clean_lines: list[str] = []

        for rl in raw_lines:
            stripped = rl.strip()
            # [UPPERCASE TAG] at start = speaker label
            speaker_match = re.match(r"^\[([A-Z][A-Z ]*[A-Z])\]\s*(.*)", stripped)
            if speaker_match:
                potential_speaker = speaker_match.group(1)
                remainder = speaker_match.group(2).strip()
                if remainder or len(potential_speaker.split()) == 1:
                    speaker = potential_speaker
                    if remainder:
                        clean_lines.append(remainder)
                else:
                    speaker = potential_speaker
                continue

            # [sound effect] entire line = SFX
            sfx_match = re.match(r"^\[([^\]]+)\]$", stripped)
            if sfx_match:
                inner = sfx_match.group(1)
                if inner == inner.upper() and re.match(r"^[A-Z][A-Z ]*[A-Z]$", inner):
                    # Standalone uppercase tag = speaker
                    speaker = inner
                else:
                    sfx_tags.append(inner)
                continue

            # Remove inline SFX tags (lowercase/mixed)
            cleaned = re.sub(
                r"\[([^\]]*)\]",
                lambda m: "" if (m.group(1) != m.group(1).upper() or len(m.group(1)) <= 2) else "",
                stripped,
            )
            if cleaned.strip():
                clean_lines.append(cleaned.strip())

        clean_text = " ".join(clean_lines).strip()

        subtitles.append({
            "id": seq,
            "start_sec": round(start_sec, 3),
            "end_sec": round(end_sec, 3),
            "speaker": speaker,
            "sfx": sfx_tags if sfx_tags else None,
            "text": clean_text,
            "raw_text": raw_text,
        })

    # Forward-fill speaker tags for consecutive lines
    last_speaker = None
    for sub in subtitles:
        if sub["speaker"]:
            last_speaker = sub["speaker"]
        elif last_speaker and not sub["sfx"] and sub["text"]:
            sub["speaker"] = last_speaker

    return subtitles


# ── Phase 2: Scene Segmentation ────────────────────────────────────────────

MIN_SCENE_GAP = 3.0
MIN_SCENE_DURATION = 15.0


def segment_scenes(subtitles: list[dict]) -> list[dict]:
    """Break subtitle stream into logical scenes based on time gaps."""
    if not subtitles:
        return []

    scenes: list[dict] = []
    scene_start = subtitles[0]["start_sec"]
    scene_subs: list[int] = [subtitles[0]["id"]]

    for i in range(1, len(subtitles)):
        prev = subtitles[i - 1]
        curr = subtitles[i]
        gap = curr["start_sec"] - prev["end_sec"]

        if gap >= MIN_SCENE_GAP:
            scenes.append({
                "id": len(scenes) + 1,
                "start": round(scene_start, 3),
                "end": round(prev["end_sec"], 3),
                "label": "",
                "subtitle_ids": scene_subs,
                "duration_sec": round(prev["end_sec"] - scene_start, 3),
            })
            scene_start = curr["start_sec"]
            scene_subs = [curr["id"]]
        else:
            scene_subs.append(curr["id"])

    # Close last scene
    scenes.append({
        "id": len(scenes) + 1,
        "start": round(scene_start, 3),
        "end": round(subtitles[-1]["end_sec"], 3),
        "label": "",
        "subtitle_ids": scene_subs,
        "duration_sec": round(subtitles[-1]["end_sec"] - scene_start, 3),
    })

    # Merge tiny scenes
    merged = [scenes[0]]
    for scene in scenes[1:]:
        prev = merged[-1]
        if prev["duration_sec"] < MIN_SCENE_DURATION:
            merged[-1] = {
                "id": prev["id"],
                "start": prev["start"],
                "end": scene["end"],
                "label": "",
                "subtitle_ids": prev["subtitle_ids"] + scene["subtitle_ids"],
                "duration_sec": round(scene["end"] - prev["start"], 3),
            }
        elif scene["duration_sec"] < MIN_SCENE_DURATION:
            merged[-1] = {
                "id": prev["id"],
                "start": prev["start"],
                "end": scene["end"],
                "label": "",
                "subtitle_ids": prev["subtitle_ids"] + scene["subtitle_ids"],
                "duration_sec": round(scene["end"] - prev["start"], 3),
            }
        else:
            merged.append(scene)

    scenes = merged

    # Label scenes
    sub_map = {s["id"]: s for s in subtitles}
    for scene in scenes:
        scene_subs = [sub_map[sid] for sid in scene["subtitle_ids"] if sid in sub_map]
        if not scene_subs:
            scene["label"] = f'Scene {scene["id"]}'
            continue

        speaker_lines: dict[str, int] = Counter()
        first_text = ""
        for sub in scene_subs:
            if sub["speaker"]:
                speaker_lines[sub["speaker"]] += 1
            if sub["text"] and not first_text and not sub["sfx"]:
                first_text = sub["text"][:50]

        dominant = speaker_lines.most_common(1)[0][0] if speaker_lines else ""
        if dominant and first_text:
            scene["label"] = f"{dominant}: {first_text}"
        elif dominant:
            scene["label"] = dominant
        elif first_text:
            scene["label"] = first_text
        else:
            scene["label"] = f'Scene {scene["id"]}'

    return scenes


# ── Phase 3: Character Analysis ────────────────────────────────────────────

def analyze_characters(subtitles: list[dict], scenes: list[dict]) -> list[dict]:
    """Build character profiles from subtitle data."""
    speakers: dict[str, dict] = {}

    for sub in subtitles:
        sp = sub["speaker"] or "unknown"
        if sp not in speakers:
            speakers[sp] = {
                "name": sp,
                "lines": 0,
                "words": 0,
                "total_speaking_time": 0.0,
                "first_appearance": sub["start_sec"],
                "last_appearance": sub["end_sec"],
                "line_lengths": [],
            }
        c = speakers[sp]
        c["lines"] += 1
        word_count = len(sub["text"].split()) if sub["text"] else 0
        c["words"] += word_count
        c["total_speaking_time"] += round(sub["end_sec"] - sub["start_sec"], 3)
        c["line_lengths"].append(word_count)
        c["first_appearance"] = min(c["first_appearance"], sub["start_sec"])
        c["last_appearance"] = max(c["last_appearance"], sub["end_sec"])

    # Interaction matrix
    interactions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for i in range(1, len(subtitles)):
        prev_sp = subtitles[i - 1]["speaker"] or "unknown"
        curr_sp = subtitles[i]["speaker"] or "unknown"
        if prev_sp != curr_sp:
            interactions[prev_sp][curr_sp] += 1

    characters = []
    for name, c in sorted(speakers.items(), key=lambda x: -x[1]["lines"]):
        avg_line_length = round(float(np.mean(c["line_lengths"])), 1) if c["line_lengths"] else 0
        characters.append({
            "name": c["name"],
            "lines": c["lines"],
            "words": c["words"],
            "total_speaking_time": round(c["total_speaking_time"], 1),
            "avg_line_length": avg_line_length,
            "first_appearance": round(c["first_appearance"], 1),
            "last_appearance": round(c["last_appearance"], 1),
            "screen_presence": round(c["last_appearance"] - c["first_appearance"], 1),
            "interactions": dict(interactions.get(name, {})),
        })

    return characters


# ── Phase 4: Sentiment & Emotional Analysis ─────────────────────────────────

def _classify_emotion(text: str, compound: float) -> str:
    """Classify emotion based on keyword heuristics and sentiment compound."""
    text_lower = text.lower()
    emotion_scores: dict[str, int] = {}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                emotion_scores[emotion] = emotion_scores.get(emotion, 0) + 1

    if not emotion_scores:
        if compound >= 0.5:
            return "hope"
        elif compound >= 0.05:
            return "neutral"
        elif compound <= -0.5:
            return "despair"
        else:
            return "fear"

    return max(emotion_scores, key=emotion_scores.get)


def analyze_sentiment(subtitles: list[dict], scenes: list[dict]) -> tuple[list[dict], list[dict]]:
    """Score each subtitle and scene for sentiment/emotion."""
    # Per-subtitle sentiment
    for sub in subtitles:
        if sub["text"]:
            scores = SENTIMENT_ENGINE.polarity_scores(sub["text"])
            sub["sentiment"] = {
                "compound": round(scores["compound"], 4),
                "pos": round(scores["pos"], 4),
                "neu": round(scores["neu"], 4),
                "neg": round(scores["neg"], 4),
            }
            sub["emotion"] = _classify_emotion(sub["text"], scores["compound"])
        else:
            sub["sentiment"] = {"compound": 0, "pos": 0, "neu": 1, "neg": 0}
            sub["emotion"] = "neutral"

    # Per-scene emotional arc
    sub_map = {s["id"]: s for s in subtitles}
    emotional_arc = []

    for scene in scenes:
        scene_subs = [sub_map[sid] for sid in scene["subtitle_ids"] if sid in sub_map]
        if not scene_subs:
            emotional_arc.append({
                "scene_id": scene["id"],
                "label": scene["label"],
                "start": scene["start"],
                "end": scene["end"],
                "avg_compound": 0,
                "dominant_emotion": "neutral",
                "emotion_counts": {},
            })
            continue

        total_weight = 0
        weighted_compound = 0.0
        emotion_counts: dict[str, int] = Counter()

        for sub in scene_subs:
            weight = max(len(sub["text"].split()), 1)
            weighted_compound += sub["sentiment"]["compound"] * weight
            total_weight += weight
            emotion_counts[sub["emotion"]] += 1

        avg_compound = round(weighted_compound / total_weight, 4) if total_weight > 0 else 0
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"

        emotional_arc.append({
            "scene_id": scene["id"],
            "label": scene["label"],
            "start": scene["start"],
            "end": scene["end"],
            "avg_compound": avg_compound,
            "dominant_emotion": dominant_emotion,
            "emotion_counts": dict(emotion_counts),
        })

    # Smooth with rolling window
    compounds = [a["avg_compound"] for a in emotional_arc]
    window = 5
    for i in range(len(compounds)):
        start_i = max(0, i - window // 2)
        end_i = min(len(compounds), i + window // 2 + 1)
        emotional_arc[i]["smoothed_compound"] = round(float(np.mean(compounds[start_i:end_i])), 4)

    return subtitles, emotional_arc


# ── Phase 5: Theme Extraction ──────────────────────────────────────────────

def extract_themes(subtitles: list[dict], scenes: list[dict]) -> dict:
    """Extract themes per scene using keyword matching."""
    sub_map = {s["id"]: s for s in subtitles}

    scene_themes = []
    theme_arcs = {theme: [] for theme in THEME_KEYWORDS}

    for scene in scenes:
        scene_subs = [sub_map[sid] for sid in scene["subtitle_ids"] if sid in sub_map]
        scene_text = " ".join(sub["text"] for sub in scene_subs if sub["text"]).lower()

        theme_scores = {}
        for theme, keywords in THEME_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in scene_text)
            total_words = len(scene_text.split()) if scene_text else 1
            score = round(hits / max(total_words, 1) * 100, 2)
            theme_scores[theme] = score
            theme_arcs[theme].append({
                "scene_id": scene["id"],
                "start": scene["start"],
                "score": score,
            })

        dominant = max(theme_scores, key=theme_scores.get) if any(theme_scores.values()) else None

        scene_themes.append({
            "scene_id": scene["id"],
            "label": scene["label"],
            "start": scene["start"],
            "end": scene["end"],
            "theme_scores": theme_scores,
            "dominant_theme": dominant,
        })

    return {
        "theme_definitions": THEME_KEYWORDS,
        "scene_themes": scene_themes,
        "theme_arcs": theme_arcs,
    }


# ── Phase 6: Dialogue Pattern Analysis ──────────────────────────────────────

CONVERSATION_GAP = 5.0


def analyze_dialogue(subtitles: list[dict], scenes: list[dict]) -> tuple[dict, dict]:
    """Analyze dialogue patterns, conversation dynamics, and generate barcode data."""
    sub_map = {s["id"]: s for s in subtitles}

    # Per-scene pattern classification
    scene_patterns = []
    for scene in scenes:
        scene_subs = [sub_map[sid] for sid in scene["subtitle_ids"] if sid in sub_map]

        speaker_words: dict[str, int] = defaultdict(int)
        speaker_lines: dict[str, int] = defaultdict(int)
        has_narration = False
        total_lines = len(scene_subs)

        for sub in scene_subs:
            sp = sub["speaker"] or "unknown"
            words = len(sub["text"].split()) if sub["text"] else 0
            speaker_words[sp] += words
            speaker_lines[sp] += 1
            if not sub["speaker"] and sub["text"]:
                has_narration = True

        total_words = sum(speaker_words.values())
        if total_words == 0:
            pattern = "narration"
        else:
            top_speaker = max(speaker_words, key=speaker_words.get)
            top_ratio = speaker_words[top_speaker] / total_words
            if top_ratio > 0.7:
                pattern = "monologue"
            elif len(speaker_words) == 1:
                pattern = "monologue"
            elif has_narration and total_lines < 5:
                pattern = "narration"
            else:
                pattern = "dialogue"

        scene_patterns.append({
            "scene_id": scene["id"],
            "label": scene["label"],
            "start": scene["start"],
            "end": scene["end"],
            "pattern": pattern,
            "speaker_words": dict(speaker_words),
            "speaker_lines": dict(speaker_lines),
            "total_words": total_words,
            "total_lines": total_lines,
        })

    # Conversation detection
    conversations = []
    current_conv: list[dict] = []
    for sub in subtitles:
        if not sub["speaker"] or sub["speaker"] == "unknown":
            continue

        if not current_conv:
            current_conv = [sub]
        else:
            gap = sub["start_sec"] - current_conv[-1]["end_sec"]
            if gap <= CONVERSATION_GAP and sub["speaker"] != current_conv[-1].get("speaker"):
                current_conv.append(sub)
            else:
                if len(current_conv) >= 2:
                    conversations.append(current_conv)
                current_conv = [sub]

    if len(current_conv) >= 2:
        conversations.append(current_conv)

    # Turn-taking metrics
    conv_metrics = []
    for conv in conversations:
        turns = len(conv)
        speakers_in_conv = list(dict.fromkeys(s["speaker"] for s in conv if s["speaker"]))
        avg_gap = round(
            float(np.mean([conv[i]["start_sec"] - conv[i - 1]["end_sec"] for i in range(1, len(conv))])),
            2,
        ) if len(conv) > 1 else 0
        dominance = {}
        for sp in speakers_in_conv:
            dominance[sp] = sum(1 for s in conv if s["speaker"] == sp)

        conv_metrics.append({
            "turns": turns,
            "speakers": speakers_in_conv,
            "avg_gap_sec": avg_gap,
            "dominance": dominance,
        })

    # Movie barcode: words per 10-second window
    total_duration = subtitles[-1]["end_sec"] if subtitles else 0
    window = 10.0
    barcode = []
    for start in np.arange(0, total_duration, window):
        end = start + window
        words_in_window = 0
        subs_in_window = 0
        for sub in subtitles:
            if sub["start_sec"] < end and sub["end_sec"] > start:
                words_in_window += len(sub["text"].split()) if sub["text"] else 0
                subs_in_window += 1
        barcode.append({
            "start": round(float(start), 1),
            "end": round(float(end), 1),
            "words": words_in_window,
            "subtitle_count": subs_in_window,
        })

    dialogue_data = {
        "scene_patterns": scene_patterns,
        "conversations": conv_metrics[:50],
        "total_conversations": len(conversations),
        "pattern_counts": dict(Counter(sp["pattern"] for sp in scene_patterns)),
    }

    barcode_data = {
        "window_sec": window,
        "total_duration_sec": round(total_duration, 1),
        "barcode": barcode,
    }

    return dialogue_data, barcode_data


# ── Main Pipeline ──────────────────────────────────────────────────────────

def save_json(data, name: str) -> Path:
    """Save data to cache directory."""
    path = CACHE_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ {path} ({len(json.dumps(data))} bytes)")
    return path


def main() -> None:
    print("🎬 Project Hail Mary — Analysis Pipeline")
    print("=" * 50)

    # Phase 1: Parse SRT
    print("\n📖 Phase 1: Parsing SRT...")
    subtitles = parse_srt(SRT_PATH)
    print(f"  Parsed {len(subtitles)} subtitle entries")
    speakers = Counter(s["speaker"] for s in subtitles if s["speaker"])
    print(f"  Speakers: {', '.join(f'{k}({v})' for k, v in speakers.most_common(10))}")
    save_json(subtitles, "subtitles")

    # Phase 2: Scene Segmentation
    print("\n🎬 Phase 2: Segmenting scenes...")
    scenes = segment_scenes(subtitles)
    print(f"  Found {len(scenes)} scenes")
    save_json(scenes, "scenes")

    # Phase 3: Character Analysis
    print("\n👥 Phase 3: Analyzing characters...")
    characters = analyze_characters(subtitles, scenes)
    print(f"  Found {len(characters)} characters")
    for c in characters[:5]:
        print(f"    {c['name']}: {c['lines']} lines, {c['words']} words")
    save_json(characters, "characters")

    # Phase 4: Sentiment & Emotional Analysis
    print("\n💭 Phase 4: Analyzing sentiment...")
    subtitles, emotional_arc = analyze_sentiment(subtitles, scenes)
    print(f"  Scored {len(subtitles)} subtitles, {len(emotional_arc)} scene arcs")
    emotion_counts = Counter(e["dominant_emotion"] for e in emotional_arc)
    print(f"  Emotions: {', '.join(f'{k}({v})' for k, v in emotion_counts.most_common())}")
    save_json([s["sentiment"] for s in subtitles], "sentiment")
    save_json(emotional_arc, "emotional_arc")

    # Phase 5: Theme Extraction
    print("\n🔍 Phase 5: Extracting themes...")
    themes = extract_themes(subtitles, scenes)
    dominant_counts = Counter(t["dominant_theme"] for t in themes["scene_themes"] if t["dominant_theme"])
    print(f"  Themes: {', '.join(f'{k}({v})' for k, v in dominant_counts.most_common())}")
    save_json(themes, "themes")

    # Phase 6: Dialogue Patterns
    print("\n💬 Phase 6: Analyzing dialogue patterns...")
    dialogue_data, barcode_data = analyze_dialogue(subtitles, scenes)
    print(f"  Patterns: {dialogue_data['pattern_counts']}")
    print(f"  Conversations: {dialogue_data['total_conversations']}")
    save_json(dialogue_data, "dialogue_patterns")
    save_json(barcode_data, "movie_barcode")

    print("\n✅ Pipeline complete! All artifacts saved to data/cache/")
    print("   Run `make serve` or `uv run streamlit run app.py` to view the dashboard.")


if __name__ == "__main__":
    main()