import os
import re
import pandas as pd
import numpy as np
import spacy
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Curated scientific jargon for Project Hail Mary
JARGON_GLOSSARY = {
    'astrophage', 'petrova', 'xenonite', 'ammonia', 'eruption', 'orbital', 'radiation', 
    'light-year', 'blip-a', 'hail mary', 'leak', 'generator', 'thrust', 'fuel', 
    'spectrometry', 'gravity', 'atmosphere', 'nitrogen', 'wavelength', 'nanometer', 
    'einstein', 'relativity', 'fusion', 'helium', 'hydrogen', 'xenon', 'temperature', 
    'celsius', 'kelvin', 'newton', 'force', 'speed', 'velocity', 'particle', 
    'magnetic', 'frequency', 'photon', 'luminosity', 'tau ceti', 'sol', 'sun', 
    'star', 'planet', 'orbit', 'trajectory', 'mass', 'density', 'pressure', 'vacuum', 
    'silica', 'coma', 'amnesia', 'lab', 'biology', 'culture', 'experiment', 'petri'
}

# Guided topic keywords
TOPIC_KEYWORDS = {
    'space_physics': [
        'astrophage', 'petrova', 'light', 'orbit', 'sun', 'solar', 'radiation', 'energy', 
        'wavelength', 'speed', 'science', 'einstein', 'gravity', 'velocity', 'particle', 
        'fusion', 'helium', 'hydrogen', 'xenon', 'temperature', 'celsius', 'kelvin', 'newton',
        'star', 'planet', 'tau ceti', 'mass', 'density', 'pressure', 'vacuum', 'trajectory'
    ],
    'rocky_contact': [
        'rocky', 'friend', 'musical', 'alien', 'sound', 'notes', 'language', 'translate', 
        'understand', 'fist', 'bump', 'happy', 'point', 'watch', 'ammonia', 'xenonite', 
        'atmosphere', 'question', 'yes', 'no', 'hear', 'voice', 'sing', 'chord', 'spider'
    ],
    'danger_survival': [
        'emergency', 'leak', 'danger', 'die', 'save', 'air', 'oxygen', 'pressure', 'fuel', 
        'generator', 'thrust', 'breach', 'warning', 'damage', 'explode', 'structural', 
        'coma', 'robot', 'medical', 'kill', 'destroy', 'broken', 'heat', 'cold', 'fix', 'repair'
    ],
    'earth_flashback': [
        'stratt', 'eva', 'project', 'hail mary', 'mission', 'earth', 'un', 'government', 
        'nuke', 'authority', 'legal', 'launch', 'crew', 'china', 'america', 'scientist', 
        'laboratory', 'military', 'command', 'officer', 'court', 'approve', 'sign', 'funding'
    ]
}

def time_to_seconds(t_str):
    try:
        h, m, s = t_str.split(':')
        s, ms = s.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + float(ms) / 1000.0
    except:
        return 0.0

def approx_syllables(text):
    words = text.lower().split()
    syllable_count = 0
    for word in words:
        word = re.sub(r'[^a-z]', '', word)
        vowels = "aeiouy"
        count = 0
        if not word:
            continue
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count <= 0:
            count = 1
        syllable_count += count
    return syllable_count

def calculate_complexity(text):
    words = [w for w in text.split() if w]
    word_count = len(words)
    if word_count == 0:
        return 1.0, 0.0, 0.0
    
    # Estimate sentences
    sentence_count = max(1, text.count('.') + text.count('?') + text.count('!'))
    asl = word_count / sentence_count
    
    # Syllables
    syllables = approx_syllables(text)
    asw = syllables / word_count
    
    # Flesch-Kincaid Grade Level
    fk_grade = (0.39 * asl) + (11.8 * asw) - 15.59
    fk_grade = max(1.0, min(18.0, fk_grade))  # Cap between 1st grade and college grad (18)
    
    # Jargon Density
    clean_words = [re.sub(r'[^a-z]', '', w.lower()) for w in words]
    jargon_count = sum(1 for w in clean_words if w in JARGON_GLOSSARY)
    jargon_density = (jargon_count / word_count) * 100.0
    
    # Type-Token Ratio (Vocabulary diversity)
    ttr = len(set(clean_words)) / word_count if word_count > 0 else 0.0
    
    return round(fk_grade, 1), round(jargon_density, 1), round(ttr, 2)

def predict_speaker_heuristic(text, time_sec, sentiment):
    text_lower = text.lower()
    
    # Direct clues for Rocky
    rocky_clues = {
        'rocky', 'friend', 'fist', 'bump', 'question', 'happy', 'point', 'watch', 'ammonia', 
        'xenonite', 'bad bad', 'happy happy', 'thank friend', 'sing', 'musical', 'notes',
        'understand', 'no understand', 'yes question', 'good good', 'you point', 'i point'
    }
    
    # Direct clues for Stratt
    stratt_clues = {
        'stratt', 'eva', 'project', 'hail mary', 'mission', 'un', 'court', 'authority', 
        'legal', 'nuke', 'nukes', 'nuking', 'launch', 'committee', 'china', 'russia', 
        'united nations', 'funding', 'order', 'command', 'redell', 'lekell', 'du bois'
    }
    
    # Rocky's sentence structure patterns (e.g. repetitive short expressions, no auxiliary verbs)
    rocky_pattern = (
        'happy' in text_lower or 
        'friend' in text_lower or
        'question' in text_lower or
        re.search(r'\b(good|bad|happy|yes|no)\b.*\b\1\b', text_lower)
    )
    
    # Rule 1: Rocky mentions or conversational indicators
    rocky_score = sum(1 for clue in rocky_clues if clue in text_lower)
    if rocky_pattern:
        rocky_score += 2
        
    # Rule 2: Stratt/Earth Flashback indicators
    stratt_score = sum(1 for clue in stratt_clues if clue in text_lower)
    
    # Time-based prior:
    # 0 to 15 minutes: Grace waking up from coma (mostly Grace, a few Earth flashbacks/recordings)
    # 15 to 45 minutes: First contact (Grace & Rocky)
    # Flashbacks are interspersed throughout, but Earth team is heavily dominant in specific conversations.
    if stratt_score > rocky_score and stratt_score >= 1:
        return "Eva Stratt"
    elif rocky_score > stratt_score and rocky_score >= 1:
        return "Rocky"
    
    # Scientific terms or narrative observations point to Grace
    science_score = sum(1 for jargon in JARGON_GLOSSARY if jargon in text_lower)
    if 'i ' in text_lower or 'my ' in text_lower or science_score > 1:
        return "Ryland Grace"
        
    # Default to Ryland Grace (narrative lead) or Rocky/Stratt based on proximity
    # If the sentence is extremely short and has simple grammar, could be Rocky
    if len(text.split()) <= 4 and ('yes' in text_lower or 'no' in text_lower or 'good' in text_lower):
        return "Rocky"
        
    return "Ryland Grace"

def compute_topics(text):
    text_lower = text.lower()
    words = [re.sub(r'[^a-z]', '', w) for w in text_lower.split() if w]
    if not words:
        return 0.0, 0.0, 0.0, 0.0, 1.0
        
    scores = {}
    total_score = 0.0
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for w in words if w in keywords)
        scores[topic] = float(score)
        total_score += float(score)
        
    if total_score == 0.0:
        # Default is general dialogue
        return 0.0, 0.0, 0.0, 0.0, 1.0
        
    # Normalize and return
    return (
        round(scores['space_physics'] / total_score, 2),
        round(scores['rocky_contact'] / total_score, 2),
        round(scores['danger_survival'] / total_score, 2),
        round(scores['earth_flashback'] / total_score, 2),
        0.0  # General dialogue is 0 since we matched specific keywords
    )

def assign_narrative_act(time_sec, total_duration):
    pct = time_sec / total_duration if total_duration > 0 else 0.0
    if pct <= 0.15:
        return "Exposition"
    elif pct <= 0.75:
        return "Rising Action"
    elif pct <= 0.90:
        return "Climax"
    else:
        return "Resolution"

def main():
    load_dotenv()
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASS", "postgres")
    db_name = os.getenv("DB_NAME", "postgres")

    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_path = os.path.join(base_dir, 'outputs', 'subtitles.csv')
    
    print(f"Loading subtitles from {input_path}...")
    df = pd.read_csv(input_path)
    
    df['time_sec'] = df['start_time'].apply(time_to_seconds)
    df = df.sort_values('time_sec').reset_index(drop=True)
    
    total_movie_duration = df['time_sec'].max()
    
    print("Running advanced NLP calculations...")
    sia = SentimentIntensityAnalyzer()
    
    sentiment_scores = []
    readability_grades = []
    jargon_densities = []
    ttrs = []
    speakers = []
    space_physics = []
    rocky_contact = []
    danger_survival = []
    earth_flashback = []
    general_dialogue = []
    narrative_acts = []
    word_counts = []
    
    for idx, row in df.iterrows():
        text = str(row['text'])
        words = text.split()
        word_counts.append(len(words))
        
        # 1. Sentiment
        score = sia.polarity_scores(text)['compound']
        sentiment_scores.append(score)
        
        # 2. Complexity
        grade, jargon, ttr = calculate_complexity(text)
        readability_grades.append(grade)
        jargon_densities.append(jargon)
        ttrs.append(ttr)
        
        # 3. Speaker
        speaker = predict_speaker_heuristic(text, row['time_sec'], score)
        speakers.append(speaker)
        
        # 4. Topics
        sp, rc, ds, ef, gd = compute_topics(text)
        space_physics.append(sp)
        rocky_contact.append(rc)
        danger_survival.append(ds)
        earth_flashback.append(ef)
        
        # If all guided topics are 0, general dialogue is 1.0
        if sp == 0.0 and rc == 0.0 and ds == 0.0 and ef == 0.0:
            general_dialogue.append(1.0)
        else:
            general_dialogue.append(0.0)
            
        # 5. Narrative Act
        act = assign_narrative_act(row['time_sec'], total_movie_duration)
        narrative_acts.append(act)
        
    df['sentiment_score'] = sentiment_scores
    df['word_count'] = word_counts
    df['readability_grade'] = readability_grades
    df['jargon_density'] = jargon_densities
    df['vocabulary_diversity'] = ttrs
    df['predicted_speaker'] = speakers
    df['topic_space_physics'] = space_physics
    df['topic_rocky_contact'] = rocky_contact
    df['topic_danger_survival'] = danger_survival
    df['topic_earth_flashback'] = earth_flashback
    df['topic_general_dialogue'] = general_dialogue
    df['narrative_act'] = narrative_acts
    
    # Export Line-Level Advanced CSV
    output_path = os.path.join(base_dir, 'outputs', 'subtitles_advanced.csv')
    df.to_csv(output_path, index=False)
    print(f"Saved line-level advanced subtitles to: {output_path}")
    
    # Group into 2-minute "scenes" for aggregated analytics
    print("Generating scene-level aggregated analytics...")
    df['minute_window'] = (df['time_sec'] // 120) * 2  # 2 minute intervals
    
    scene_aggregates = []
    for minute, group in df.groupby('minute_window'):
        scene_text = " ".join(group['text'].fillna("").tolist())
        start_time_str = group['start_time'].iloc[0]
        
        # Complexity averages
        avg_grade = group['readability_grade'].mean()
        avg_jargon = group['jargon_density'].mean()
        avg_vocab = group['vocabulary_diversity'].mean()
        avg_sentiment = group['sentiment_score'].mean()
        
        # Dominant Speaker
        dominant_speaker = group['predicted_speaker'].value_counts().index[0]
        
        # Topics
        avg_sp = group['topic_space_physics'].mean()
        avg_rc = group['topic_rocky_contact'].mean()
        avg_ds = group['topic_danger_survival'].mean()
        avg_ef = group['topic_earth_flashback'].mean()
        avg_gd = group['topic_general_dialogue'].mean()
        
        # Speaking Rate (Words per minute in this window)
        words_count = group['word_count'].sum()
        wpm = words_count / 2.0  # 2 minute window
        
        act = group['narrative_act'].iloc[0]
        
        scene_aggregates.append({
            'minute_window': int(minute),
            'start_time': start_time_str,
            'text': scene_text,
            'avg_sentiment': round(avg_sentiment, 3),
            'avg_readability_grade': round(avg_grade, 1),
            'avg_jargon_density': round(avg_jargon, 1),
            'avg_vocab_diversity': round(avg_vocab, 2),
            'dominant_speaker': dominant_speaker,
            'speaking_rate_wpm': round(wpm, 1),
            'topic_space_physics': round(avg_sp, 2),
            'topic_rocky_contact': round(avg_rc, 2),
            'topic_danger_survival': round(avg_ds, 2),
            'topic_earth_flashback': round(avg_ef, 2),
            'topic_general_dialogue': round(avg_gd, 2),
            'narrative_act': act
        })
        
    scenes_df = pd.DataFrame(scene_aggregates)
    scenes_output_path = os.path.join(base_dir, 'outputs', 'scenes_advanced.csv')
    scenes_df.to_csv(scenes_output_path, index=False)
    print(f"Saved aggregated scene dataset to: {scenes_output_path}")
    
    # Upload to PostgreSQL Database
    try:
        connection_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(connection_url)
        
        # Write both tables to database
        df.to_sql('subtitles_advanced', engine, if_exists='replace', index=False)
        print("Successfully uploaded 'subtitles_advanced' table to PostgreSQL.")
        
        scenes_df.to_sql('scenes_advanced', engine, if_exists='replace', index=False)
        print("Successfully uploaded 'scenes_advanced' table to PostgreSQL.")
    except Exception as e:
        print(f"Error uploading to database: {e}")

if __name__ == "__main__":
    main()
