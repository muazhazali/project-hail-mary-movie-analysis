import os
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
import spacy
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px
import warnings

def time_to_seconds(t_str):
    """Convert HH:MM:SS.mmm to total seconds."""
    try:
        h, m, s = t_str.split(':')
        s, ms = s.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + float(ms) / 1000.0
    except:
        return 0

def main():
    warnings.filterwarnings('ignore')

    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_dir, 'outputs', 'subtitles.csv')
    visuals_dir = os.path.join(base_dir, 'outputs', 'visuals')
    os.makedirs(visuals_dir, exist_ok=True)

    print(f"Loading subtitles from {data_path}")
    df = pd.read_csv(data_path)

    # Initialize NLP tools
    print("Initializing NLP tools (VADER & SpaCy)...")
    sia = SentimentIntensityAnalyzer()
    nlp = spacy.load("en_core_web_sm")
    stop_words = set(stopwords.words('english'))

    # ==========================================
    # 1. Word Frequency Analysis
    # ==========================================
    print("Performing Word Frequency Analysis...")
    all_text = " ".join(df['text'].fillna("").tolist())
    doc = nlp(all_text)

    keywords = []
    for token in doc:
        # Extract Nouns and Proper Nouns for technical terms and characters
        if token.pos_ in ['NOUN', 'PROPN'] and token.text.lower() not in stop_words and len(token.text) > 2:
            keywords.append(token.text.lower())

    word_counts = pd.Series(keywords).value_counts().head(30)

    # Word Cloud
    print("Generating Word Cloud...")
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Most Common Terms & Characters')
    wc_path = os.path.join(visuals_dir, 'wordcloud.png')
    plt.savefig(wc_path)
    plt.close()

    # Bar Chart
    print("Generating Keyword Bar Chart...")
    fig_bar = px.bar(x=word_counts.values, y=word_counts.index, orientation='h', title='Top 30 Keywords')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    bar_path = os.path.join(visuals_dir, 'keywords_barchart.html')
    fig_bar.write_html(bar_path)

    # ==========================================
    # 2. Sentiment Analysis
    # ==========================================
    print("Performing Sentiment Analysis...")
    df['sentiment_score'] = df['text'].apply(lambda x: sia.polarity_scores(str(x))['compound'])

    # Time processing for rolling average
    df['time_sec'] = df['start_time'].apply(time_to_seconds)
    df = df.sort_values('time_sec')

    # Group by 5-minute (300s) windows to smooth out the timeline
    df['window_5min'] = df['time_sec'] // 300
    sentiment_timeline = df.groupby('window_5min')['sentiment_score'].mean().reset_index()
    sentiment_timeline['minute_approx'] = sentiment_timeline['window_5min'] * 5

    # Sentiment Graph
    print("Generating Emotional Timeline...")
    fig_sent = px.line(sentiment_timeline, x='minute_approx', y='sentiment_score', 
                       title='Emotional Timeline (5-minute rolling average)',
                       labels={'minute_approx': 'Time (Minutes)', 'sentiment_score': 'Average Sentiment'})
    sent_path = os.path.join(visuals_dir, 'sentiment_timeline.html')
    fig_sent.write_html(sent_path)

    # ==========================================
    # 3. Dialogue Statistics
    # ==========================================
    print("Performing Dialogue Statistics...")
    # Speaking intensity: chars per duration
    df['char_length'] = df['text'].apply(lambda x: len(str(x)))
    # Avoid division by zero
    df['chars_per_sec'] = df['char_length'] / df['duration_sec'].replace(0, 0.1)

    # Average statistics per 5-minute window
    dialogue_stats = df.groupby('window_5min').agg(
        subtitle_density=('text', 'count'),
        avg_chars_per_sec=('chars_per_sec', 'mean')
    ).reset_index()
    dialogue_stats['minute_approx'] = dialogue_stats['window_5min'] * 5

    # Pacing / Intensity Chart
    print("Generating Dialogue Pacing Chart...")
    fig_pacing = px.line(dialogue_stats, x='minute_approx', y=['subtitle_density', 'avg_chars_per_sec'],
                         title='Dialogue Statistics & Pacing over Time',
                         labels={'value': 'Count / Rate', 'minute_approx': 'Time (Minutes)'})
    pacing_path = os.path.join(visuals_dir, 'pacing_charts.html')
    fig_pacing.write_html(pacing_path)

    print("All Stage 2 NLP Analytics complete!")
    print(f"Visualizations saved in: {visuals_dir}")

if __name__ == "__main__":
    main()
