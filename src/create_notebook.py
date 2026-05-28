import nbformat as nbf
import os

nb = nbf.v4.new_notebook()

imports = """
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
import spacy
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px
import os
import warnings
warnings.filterwarnings('ignore')
"""

setup = """
# Setup paths and load data
data_path = 'outputs/subtitles.csv'
df = pd.read_csv(data_path)

# Initialize NLP tools
sia = SentimentIntensityAnalyzer()
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))

# Create outputs directory for visuals if not exists
os.makedirs('outputs/visuals', exist_ok=True)
df.head()
"""

word_freq = """
# Extract Nouns and Proper Nouns for technical terms and characters
all_text = " ".join(df['text'].fillna("").tolist())
doc = nlp(all_text)

keywords = []
for token in doc:
    if token.pos_ in ['NOUN', 'PROPN'] and token.text.lower() not in stop_words and len(token.text) > 2:
        keywords.append(token.text.lower())

word_counts = pd.Series(keywords).value_counts().head(30)

# Visualization: Word Cloud
wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
plt.figure(figsize=(12, 6))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Most Common Terms & Characters')
plt.savefig('outputs/visuals/wordcloud.png')
plt.show()

# Visualization: Bar Chart
fig_bar = px.bar(x=word_counts.values, y=word_counts.index, orientation='h', title='Top 30 Keywords')
fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
fig_bar.write_html('outputs/visuals/keywords_barchart.html')
fig_bar.show()
"""

sentiment = """
# Calculate Sentiment Scores
df['sentiment_score'] = df['text'].apply(lambda x: sia.polarity_scores(str(x))['compound'])

# Create a rolling average of sentiment for the emotional timeline
# First we need a continuous time axis. We'll use start_time in seconds.
def time_to_seconds(t_str):
    try:
        h, m, s = t_str.split(':')
        s, ms = s.split('.')
        return int(h)*3600 + int(m)*60 + int(s) + float(ms)/1000.0
    except:
        return 0

df['time_sec'] = df['start_time'].apply(time_to_seconds)
df = df.sort_values('time_sec')

# Group by 5-minute (300s) windows to smooth out the timeline
df['window_5min'] = df['time_sec'] // 300
sentiment_timeline = df.groupby('window_5min')['sentiment_score'].mean().reset_index()
sentiment_timeline['minute_approx'] = sentiment_timeline['window_5min'] * 5

# Visualization: Sentiment Graph
fig_sent = px.line(sentiment_timeline, x='minute_approx', y='sentiment_score', 
                   title='Emotional Timeline (5-minute rolling average)',
                   labels={'minute_approx': 'Time (Minutes)', 'sentiment_score': 'Average Sentiment'})
fig_sent.write_html('outputs/visuals/sentiment_timeline.html')
fig_sent.show()
"""

stats = """
# Speaking intensity: chars per duration
df['char_length'] = df['text'].apply(lambda x: len(str(x)))
df['chars_per_sec'] = df['char_length'] / df['duration_sec'].replace(0, 0.1)

# Average sentence length per 5-minute window
dialogue_stats = df.groupby('window_5min').agg(
    subtitle_density=('text', 'count'),
    avg_chars_per_sec=('chars_per_sec', 'mean')
).reset_index()
dialogue_stats['minute_approx'] = dialogue_stats['window_5min'] * 5

# Visualization: Speaking Intensity
fig_pacing = px.line(dialogue_stats, x='minute_approx', y=['subtitle_density', 'avg_chars_per_sec'],
                     title='Dialogue Statistics & Pacing over Time',
                     labels={'value': 'Count / Rate', 'minute_approx': 'Time (Minutes)'})
fig_pacing.write_html('outputs/visuals/pacing_charts.html')
fig_pacing.show()
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell("# Stage 2: Basic NLP Analytics\\n\\nThis notebook analyzes subtitle data to extract word frequencies, character mentions, sentiment timelines, and speaking intensity."),
    nbf.v4.new_code_cell(imports),
    nbf.v4.new_code_cell(setup),
    nbf.v4.new_code_cell(word_freq),
    nbf.v4.new_code_cell(sentiment),
    nbf.v4.new_code_cell(stats)
]

# Ensure notebooks directory exists
os.makedirs('notebooks', exist_ok=True)
notebook_path = 'notebooks/01_nlp_analytics.ipynb'
with open(notebook_path, 'w') as f:
    nbf.write(nb, f)
print(f"Notebook created at {notebook_path}")
