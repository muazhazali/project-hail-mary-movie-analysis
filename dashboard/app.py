import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ---------------------------------------------
# 1. Config & Setup
# ---------------------------------------------
st.set_page_config(
    page_title="Movie Intelligence",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for extra aesthetic polish
st.markdown("""
<style>
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        color: #9061F9;
        font-weight: 800;
    }
    /* Headers */
    h1, h2, h3 {
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------
# 2. Data Loading
# ---------------------------------------------
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_dir, 'outputs', 'subtitles.csv')
    
    if not os.path.exists(data_path):
        return pd.DataFrame()
        
    df = pd.read_csv(data_path)
    
    # Calculate time in minutes for easier filtering
    def to_minutes(t_str):
        try:
            h, m, s = t_str.split(':')
            s, ms = s.split('.')
            return (int(h)*60) + int(m) + (float(s)/60.0)
        except:
            return 0.0
            
    df['minute'] = df['start_time'].apply(to_minutes)
    df['minute'] = df['minute'].round(2)
    
    # Simple keyword/character extraction for the dashboard stats
    # We look for capitalized words that aren't at the start of a sentence
    # This is a basic approximation for quick dashboard filtering
    def extract_entities(text):
        if not isinstance(text, str): return []
        # Find capitalized words
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        return words
        
    df['entities'] = df['text'].apply(extract_entities)
    
    return df

df = load_data()

if df.empty:
    st.error("No data found! Please make sure `outputs/subtitles.csv` exists (run Stage 1 & 2 first).")
    st.stop()

# ---------------------------------------------
# 3. Sidebar Filters
# ---------------------------------------------
st.sidebar.title("🎬 Movie Intelligence")
st.sidebar.markdown("Filter the insights dynamically.")

# A. Timestamp Slider
min_time = float(df['minute'].min())
max_time = float(df['minute'].max())
time_range = st.sidebar.slider(
    "Timeline (Minutes)",
    min_value=min_time,
    max_value=max_time,
    value=(min_time, max_time)
)

# B. Emotion / Sentiment Filter
# (assuming 'sentiment_score' exists from Stage 2. If it doesn't, we handle gracefully)
has_sentiment = 'sentiment_score' in df.columns

if has_sentiment:
    sentiment_range = st.sidebar.slider(
        "Emotion Filter (Compound Score)",
        min_value=-1.0, max_value=1.0,
        value=(-1.0, 1.0)
    )
else:
    sentiment_range = (-1.0, 1.0)
    st.sidebar.warning("Sentiment score not found. Please run Stage 2 NLP Analytics.")

# C. Character/Keyword Search
search_term = st.sidebar.text_input("Search Character / Keyword", "")

# Apply Filters
mask = (df['minute'] >= time_range[0]) & (df['minute'] <= time_range[1])

if has_sentiment:
    mask = mask & (df['sentiment_score'] >= sentiment_range[0]) & (df['sentiment_score'] <= sentiment_range[1])

if search_term:
    mask = mask & df['text'].str.contains(search_term, case=False, na=False)

filtered_df = df[mask]

# ---------------------------------------------
# 4. Main Dashboard Area
# ---------------------------------------------
st.title("Project Hail Mary - Movie Analytics")

# Define Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Sentiment Timeline", "Character Stats", "Word Analysis"])

# --- TAB 1: Overview ---
with tab1:
    st.header("General Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Lines of Dialogue", f"{len(filtered_df):,}")
    
    total_duration = filtered_df['duration_sec'].sum() if 'duration_sec' in filtered_df.columns else 0
    col2.metric("Total Speaking Time", f"{total_duration/60:.1f} mins")
    
    avg_len = filtered_df['text'].str.len().mean() if not filtered_df.empty else 0
    col3.metric("Avg Line Length", f"{avg_len:.0f} chars")
    
    if has_sentiment:
        avg_sent = filtered_df['sentiment_score'].mean()
        col4.metric("Avg Sentiment", f"{avg_sent:.2f}")

    st.subheader("Raw Dialogue Data")
    # Show clean subset of columns
    display_cols = ['start_time', 'end_time', 'text']
    if has_sentiment:
        display_cols.append('sentiment_score')
    st.dataframe(filtered_df[display_cols], use_container_width=True, height=400)


# --- TAB 2: Sentiment Timeline ---
with tab2:
    st.header("Emotional Arc")
    st.markdown("Tracks the positive/negative polarity of the dialogue over the selected time range.")
    
    if has_sentiment and not filtered_df.empty:
        # We group by 2-minute windows dynamically based on the filtered data
        window_size = 2
        filtered_df['window'] = (filtered_df['minute'] // window_size) * window_size
        timeline_df = filtered_df.groupby('window')['sentiment_score'].mean().reset_index()
        
        fig = px.area(timeline_df, x='window', y='sentiment_score',
                      color_discrete_sequence=['#9061F9'],
                      labels={'window': 'Time (Minutes)', 'sentiment_score': 'Average Sentiment'},
                      title=f"Sentiment over time (Smoothed every {window_size} mins)")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        # Add a zero line to easily see positive vs negative
        fig.add_hline(y=0, line_dash="dot", annotation_text="Neutral", annotation_position="bottom right", line_color="gray")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sentiment data available for the current filter.")


# --- TAB 3: Character Stats ---
with tab3:
    st.header("Character Mentions & Stats")
    st.markdown("Frequency of capitalized entities mentioned in the dialogue.")
    
    if not filtered_df.empty:
        # Explode the entities list and count
        all_entities = filtered_df.explode('entities')['entities'].dropna()
        # Filter out common false positives (like 'The', 'A', 'I')
        ignore_words = {'The', 'A', 'I', 'It', 'You', 'He', 'She', 'They', 'We', 'This', 'That', 'In', 'On', 'And'}
        valid_entities = all_entities[~all_entities.isin(ignore_words)]
        
        entity_counts = valid_entities.value_counts().head(15).reset_index()
        entity_counts.columns = ['Entity', 'Count']
        
        if not entity_counts.empty:
            fig2 = px.bar(entity_counts, x='Count', y='Entity', orientation='h',
                          color='Count', color_continuous_scale="Purples",
                          title="Top 15 Mentioned Entities/Characters")
            fig2.update_layout(yaxis={'categoryorder':'total ascending'})
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No distinct characters/entities found in this selection.")
    else:
        st.info("No data available.")


# --- TAB 4: Word Analysis ---
with tab4:
    st.header("Dynamic Word Cloud")
    st.markdown("Visual representation of dialogue text in the selected range.")
    
    if not filtered_df.empty:
        text_corpus = " ".join(filtered_df['text'].fillna("").tolist())
        
        if len(text_corpus.strip()) > 0:
            # Generate word cloud
            wc = WordCloud(width=800, height=400, background_color='#111827', 
                           colormap='Purples', max_words=100).generate(text_corpus)
            
            fig3, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            
            # Make sure figure has transparent background matching streamlit
            fig3.patch.set_alpha(0.0)
            
            st.pyplot(fig3)
        else:
            st.info("Not enough text to generate word cloud.")
    else:
        st.info("No data available.")
