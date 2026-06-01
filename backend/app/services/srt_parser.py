import re
from dataclasses import dataclass


@dataclass
class SrtEntry:
    idx: int
    start_time: float
    end_time: float
    raw_text: str
    clean_text: str
    duration: float


def _parse_srt_time(time_str: str) -> float:
    """Convert SRT time 'HH:MM:SS,mmm' to total seconds."""
    match = re.match(r"(\d+):(\d+):(\d+),(\d+)", time_str.strip())
    if not match:
        return 0.0
    h, m, s, ms = match.groups()
    return float(h) * 3600 + float(m) * 60 + float(s) + float(ms) / 1000.0


def parse_srt(content: str) -> list[SrtEntry]:
    """Parse raw SRT file content into a list of entries."""
    blocks = re.split(r"\n\s*\n", content.strip())
    entries = []
    seen_indices = set()
    
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        
        # First line should be the numeric index
        try:
            idx = int(lines[0])
        except ValueError:
            continue
        
        if len(lines) < 2:
            continue
        
        # Second line: time range
        time_match = re.match(
            r"(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)",
            lines[1]
        )
        if not time_match:
            continue
        
        start_time = _parse_srt_time(time_match.group(1))
        end_time = _parse_srt_time(time_match.group(2))
        
        # Remaining lines: text
        raw_text = "\n".join(lines[2:])
        
        # Deduplicate by index (repair malformed SRTs)
        if idx in seen_indices:
            idx = max(seen_indices) + 1
        seen_indices.add(idx)
        
        entries.append(SrtEntry(
            idx=idx,
            start_time=start_time,
            end_time=end_time,
            raw_text=raw_text,
            clean_text=raw_text,
            duration=end_time - start_time,
        ))
    
    # Sort by start time
    entries.sort(key=lambda e: e.start_time)
    return entries


def clean_text(raw: str) -> str:
    """Remove HTML tags, speaker cues, sound effects."""
    # Remove HTML tags like <i> or <b>
    text = re.sub(r"<[^>]+>", "", raw)
    # Remove speaker cues like [Mary] or [man 1]
    text = re.sub(r"\[[^\]]+\]\s*", "", text)
    # Remove leading dashes / whitespace from whole line (not internal punctuation)
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        line = re.sub(r"^[-\s]+", "", line.strip())
        if line:
            cleaned_lines.append(line)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", " ".join(cleaned_lines)).strip()
    return text.strip()


def classify_line(raw: str, cleaned: str) -> str:
    """Classify as sound_effect, dialogue, narration, or song."""
    if re.search(r"^\[[^\]]+\]\s*$", raw.strip()) or re.search(r"^\[[^\]]+\]$", raw.strip()):
        return "sound_effect"
    if raw.strip().startswith("<i>") and raw.strip().endswith("</i>"):
        return "narration"
    if "♪" in raw or re.search(r"[♪\u266A\u266B]", raw):
        return "song"
    if cleaned.strip():
        return "dialogue"
    return "other"


def extract_speaker(raw: str) -> str | None:
    """Extract a speaker name from patterns like [Mary] or [Mary] <i>text</i>."""
    match = re.search(r"^\[([^\]]+)\]", raw)
    if not match:
        return None
    candidate = match.group(1).strip()
    # Reject long bracketed strings (likely sound effects)
    if len(candidate) > 30:
        return None
    if candidate.count(" ") > 3:
        return None
    # Reject known sound-effect keywords
    sfx_keywords = {
        "breathing", "beeping", "coughing", "gagging", "groans", "thudding",
        "whirring", "choking", "music", "song", "rumbling", "splashing",
        "fades", "fading", "playing", "continues", "rapidly", "slowly",
        "creaking", "knocking", "zipper", "spits", "yelps", "clacking",
        "clicks", "buzzing", "hissing", "popping", "crackling",
    }
    lowered = candidate.lower()
    if any(kw in lowered for kw in sfx_keywords):
        return None
    # Require at least two letters (a real name)
    if not re.search(r"[a-zA-Z]{2,}", candidate):
        return None
    return candidate
