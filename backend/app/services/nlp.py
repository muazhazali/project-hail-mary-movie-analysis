import re
from collections import Counter

import spacy

_vader = None
_nlp = None


def _get_vader():
    global _vader
    if _vader is None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _vader = SentimentIntensityAnalyzer()
    return _vader


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm", disable=["parser", "textcat"])
    return _nlp


def analyze_sentiment(text: str) -> dict:
    """Return VADER sentiment scores."""
    scores = _get_vader().polarity_scores(text)
    return {
        "compound": scores["compound"],
        "pos": scores["pos"],
        "neu": scores["neu"],
        "neg": scores["neg"],
    }


def count_words(text: str) -> int:
    """Quick word count normalized by simple regex."""
    return len(re.findall(r"\b\w+\b", text))


def compute_wpm(word_count: int, duration: float) -> float | None:
    """Words per minute given duration in seconds."""
    if duration and duration > 0:
        return (word_count / duration) * 60.0
    return None


def extract_entities(texts: list[str]) -> list[tuple[str, str]]:
    """Extract named entities across a list of texts."""
    nlp = _get_nlp()
    all_entities = []
    for text in texts:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ("PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART"):
                all_entities.append((ent.text.strip(), ent.label_))
    return all_entities


def vocabulary_stats(texts: list[str]) -> dict:
    """Return total words, unique words, and most common words."""
    all_words = []
    for t in texts:
        words = re.findall(r"\b\w+\b", t.lower())
        all_words.extend(words)
    counter = Counter(all_words)
    total = len(all_words)
    unique = len(counter)
    most_common = counter.most_common(20)
    return {
        "total_words": total,
        "unique_words": unique,
        "most_common": most_common,
    }
