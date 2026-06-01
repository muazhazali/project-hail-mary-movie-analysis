import sys
import os
from collections import defaultdict

# Resolve project root and add backend to path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_BACKEND_ROOT = os.path.join(_PROJECT_ROOT, "backend")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.chdir(_BACKEND_ROOT)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(_PROJECT_ROOT, ".env"))

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models import SubtitleLine, SpeakerStat
from app.services.srt_parser import parse_srt, clean_text, classify_line, extract_speaker
from app.services.nlp import analyze_sentiment, count_words, compute_wpm, extract_entities, vocabulary_stats
from app.services.embedding import embed_texts


def ingest(srt_path: str) -> None:
    # Ensure tables / extensions exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Check if already ingested
        if db.query(SubtitleLine).count() > 0:
            print("SubtitleLine table already has data. Skipping ingestion.")
            return
        
        print(f"Reading subtitle file: {srt_path}")
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        entries = parse_srt(content)
        print(f"Parsed {len(entries)} entries")
        
        # Clean, classify, and extract metadata for each entry
        enriched = []
        for entry in entries:
            cleaned = clean_text(entry.raw_text)
            line_type = classify_line(entry.raw_text, cleaned)
            speaker = extract_speaker(entry.raw_text)
            sentiment = analyze_sentiment(cleaned or entry.raw_text)
            wc = count_words(cleaned or entry.raw_text)
            wpm = compute_wpm(wc, entry.duration)
            
            enriched.append({
                "entry": entry,
                "cleaned": cleaned,
                "line_type": line_type,
                "speaker": speaker,
                "sentiment": sentiment,
                "word_count": wc,
                "wpm": wpm,
            })
        
        # Generate embeddings in batches for memory efficiency
        batch_size = 256
        for i in range(0, len(enriched), batch_size):
            batch = enriched[i:i+batch_size]
            texts = [b["cleaned"] or b["entry"].raw_text for b in batch]
            embeddings = embed_texts(texts)
            for b, emb in zip(batch, embeddings):
                b["embedding"] = emb
            print(f"  Embedded batch {i//batch_size + 1}/{(len(enriched)-1)//batch_size + 1}")
        
        # Insert into DB
        print("Inserting into database...")
        for b in enriched:
            entry = b["entry"]
            line = SubtitleLine(
                idx=entry.idx,
                start_time=entry.start_time,
                end_time=entry.end_time,
                duration=entry.duration,
                raw_text=entry.raw_text,
                clean_text=b["cleaned"],
                line_type=b["line_type"],
                speaker=b["speaker"],
                sentiment_compound=b["sentiment"]["compound"],
                sentiment_pos=b["sentiment"]["pos"],
                sentiment_neu=b["sentiment"]["neu"],
                sentiment_neg=b["sentiment"]["neg"],
                word_count=b["word_count"],
                words_per_minute=b["wpm"],
                embedding=b["embedding"],
            )
            db.add(line)
        db.commit()
        print(f"Inserted {len(enriched)} subtitle lines")
        
        # Compute and store speaker stats
        print("Computing speaker stats...")
        speaker_lines = defaultdict(list)
        for b in enriched:
            if b["speaker"]:
                speaker_lines[b["speaker"]].append(b)
        
        speaker_texts = defaultdict(list)
        for b in enriched:
            if b["speaker"]:
                speaker_texts[b["speaker"]].append(b["cleaned"] or b["entry"].raw_text)
        
        for speaker, lines in speaker_lines.items():
            texts = speaker_texts[speaker]
            stats = vocabulary_stats(texts)
            sentiments = [b["sentiment"]["compound"] for b in lines]
            avg_sent = sum(sentiments) / len(sentiments) if sentiments else None
            wpms = [b["wpm"] for b in lines if b["wpm"] is not None]
            avg_wpm = sum(wpms) / len(wpms) if wpms else None
            
            entities = extract_entities(texts)
            # Store entities as simple 'EntityName (TYPE)' string list
            top_entities = ", ".join([f"{e[0]} ({e[1]})" for e in entities[:10]]) if entities else None
            
            stat = SpeakerStat(
                speaker=speaker,
                line_count=len(lines),
                word_count=stats["total_words"],
                unique_word_count=stats["unique_words"],
                avg_sentiment=avg_sent,
                avg_wpm=avg_wpm,
                top_entities=top_entities,
            )
            db.add(stat)
        db.commit()
        print(f"Inserted stats for {len(speaker_lines)} speakers")
        
    finally:
        db.close()


if __name__ == "__main__":
    # Default relative to the repo root
    default_path = os.path.join(
        _PROJECT_ROOT, "data",
        "Project.Hail.Mary.2026.1080p.WEB-DL.DDP5.1.Atmos.H.264-RDNYB-HI.srt"
    )
    path = sys.argv[1] if len(sys.argv) > 1 else default_path
    ingest(os.path.abspath(path))
