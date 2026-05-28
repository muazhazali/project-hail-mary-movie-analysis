import os
import re
import pandas as pd
import pysrt
from dotenv import load_dotenv
from sqlalchemy import create_engine

def clean_text(text):
    """Remove HTML tags like <i>, <b> and normalize newlines."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Replace newlines with spaces
    text = text.replace('\n', ' ').strip()
    return text

def time_to_str(subrip_time):
    """Convert pysrt.SubRipTime to HH:MM:SS.mmm format string."""
    return f"{subrip_time.hours:02d}:{subrip_time.minutes:02d}:{subrip_time.seconds:02d}.{subrip_time.milliseconds:03d}"

def time_to_seconds(subrip_time):
    """Convert pysrt.SubRipTime to total seconds."""
    return subrip_time.hours * 3600 + subrip_time.minutes * 60 + subrip_time.seconds + subrip_time.milliseconds / 1000.0

def main():
    # 1. Load Environment Variables
    load_dotenv()
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASS", "postgres")
    db_name = os.getenv("DB_NAME", "postgres")

    # 2. Parse Subtitle File
    # Searching for the srt file in data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    srt_files = [f for f in os.listdir(data_dir) if f.endswith('.srt')]
    if not srt_files:
        print("No .srt file found in data/ directory.")
        return
    
    srt_path = os.path.join(data_dir, srt_files[0])
    print(f"Parsing subtitles from: {srt_path}")
    
    subs = pysrt.open(srt_path)
    
    data = []
    for sub in subs:
        start_str = time_to_str(sub.start)
        end_str = time_to_str(sub.end)
        
        start_sec = time_to_seconds(sub.start)
        end_sec = time_to_seconds(sub.end)
        duration = end_sec - start_sec
        
        cleaned = clean_text(sub.text)
        
        if cleaned:  # Ignore empty subtitles
            data.append({
                "start_time": start_str,
                "end_time": end_str,
                "duration_sec": round(duration, 3),
                "text": cleaned
            })
            
    # 3. Create DataFrame
    df = pd.DataFrame(data)
    print(f"Extracted {len(df)} subtitle lines.")
    print(df.head())

    # 4. Export to CSV
    outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    csv_path = os.path.join(outputs_dir, 'subtitles.csv')
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV to: {csv_path}")

    # 5. Connect and Upload to PostgreSQL
    try:
        # Create SQLAlchemy engine
        connection_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(connection_url)
        
        # Write records stored in a DataFrame to a SQL database
        # if_exists='replace' will drop the table if it already exists and recreate it
        df.to_sql('subtitles', engine, if_exists='replace', index=False)
        print("Successfully uploaded subtitles to PostgreSQL database table 'subtitles'.")
    except Exception as e:
        print(f"Error connecting to or uploading to database: {e}")

if __name__ == "__main__":
    main()
