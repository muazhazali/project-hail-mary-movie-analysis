import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import requests

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
    
    def to_minutes(t_str):
        try:
            h, m, s = t_str.split(':')
            s, ms = s.split('.')
            return (int(h)*60) + int(m) + (float(s)/60.0)
        except:
            return 0.0
            
    df['minute'] = df['start_time'].apply(to_minutes).round(2)
    
    def extract_entities(text):
        if not isinstance(text, str): return []
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        return words
        
    df['entities'] = df['text'].apply(extract_entities)
    return df

df = load_data()

if df.empty:
    st.error("No data found! Please make sure `outputs/subtitles.csv` exists.")
    st.stop()

base_dir = os.path.dirname(os.path.dirname(__file__))
network_graph_path = os.path.join(base_dir, 'outputs', 'visuals', 'network_graph.html')

# ---------------------------------------------
# 3. Sidebar Filters
# ---------------------------------------------
st.sidebar.title("🎬 Movie Intelligence")
st.sidebar.markdown("Filter the insights dynamically.")

min_time = float(df['minute'].min())
max_time = float(df['minute'].max())
time_range = st.sidebar.slider("Timeline (Minutes)", min_value=min_time, max_value=max_time, value=(min_time, max_time))

has_sentiment = 'sentiment_score' in df.columns
if has_sentiment:
    sentiment_range = st.sidebar.slider("Emotion Filter (Compound Score)", min_value=-1.0, max_value=1.0, value=(-1.0, 1.0))
else:
    sentiment_range = (-1.0, 1.0)
    st.sidebar.warning("Sentiment score not found. Run Stage 2 NLP Analytics.")

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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview", "Sentiment Timeline", "Character Stats", "Word Analysis", "Network Graph", "Semantic Search"
])

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
    display_cols = ['start_time', 'end_time', 'text']
    if has_sentiment: display_cols.append('sentiment_score')
    st.dataframe(filtered_df[display_cols], use_container_width=True, height=400)

# --- TAB 2: Sentiment Timeline ---
with tab2:
    st.header("Emotional Arc")
    if has_sentiment and not filtered_df.empty:
        filtered_df['window'] = (filtered_df['minute'] // 2) * 2
        timeline_df = filtered_df.groupby('window')['sentiment_score'].mean().reset_index()
        fig = px.area(timeline_df, x='window', y='sentiment_score', color_discrete_sequence=['#9061F9'], title=f"Sentiment over time")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.add_hline(y=0, line_dash="dot", annotation_text="Neutral", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available.")

# --- TAB 3: Character Stats ---
with tab3:
    st.header("Character Mentions & Stats")
    if not filtered_df.empty:
        all_entities = filtered_df.explode('entities')['entities'].dropna()
        ignore_words = {'The', 'A', 'I', 'It', 'You', 'He', 'She', 'They', 'We', 'This', 'That', 'In', 'On', 'And'}
        valid_entities = all_entities[~all_entities.isin(ignore_words)]
        entity_counts = valid_entities.value_counts().head(15).reset_index()
        entity_counts.columns = ['Entity', 'Count']
        
        if not entity_counts.empty:
            fig2 = px.bar(entity_counts, x='Count', y='Entity', orientation='h', color='Count', color_continuous_scale="Purples")
            fig2.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No characters found in selection.")
    else:
        st.info("No data available.")

# --- TAB 4: Word Analysis ---
with tab4:
    st.header("Dynamic Word Cloud")
    if not filtered_df.empty:
        text_corpus = " ".join(filtered_df['text'].fillna("").tolist())
        if len(text_corpus.strip()) > 0:
            wc = WordCloud(width=800, height=400, background_color='#111827', colormap='Purples', max_words=100).generate(text_corpus)
            fig3, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            fig3.patch.set_alpha(0.0)
            st.pyplot(fig3)
        else:
            st.info("Not enough text.")

# --- TAB 5: Network Graph ---
with tab5:
    st.header("Character Network")
    st.markdown("Physics-based graph showing character co-occurrence.")
    if os.path.exists(network_graph_path):
        with open(network_graph_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        components.html(source_code, height=650, scrolling=True)
    else:
        st.info("Network graph not found. Run Stage 4 Analytics.")

# --- TAB 6: Semantic Search ---
with tab6:
    st.header("AI Scene Search")
    st.markdown("Search for scenes using meaning instead of exact keywords (Powered by FastAPI & pgvector).")
    
    query = st.text_input("What are you looking for?", placeholder="e.g. 'sacrifice and friendship' or 'building a space ship'")
    top_k = st.slider("Number of results", min_value=1, max_value=10, value=3)
    
    if st.button("Search"):
        if query:
            with st.spinner("Searching database..."):
                try:
                    response = requests.get(f"http://127.0.0.1:8000/search", params={"q": query, "top_k": top_k})
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])
                        if results:
                            for i, res in enumerate(results, 1):
                                st.markdown(f"### Result #{i} | Time: `{res['timestamp']}`")
                                st.success(res['dialogue'])
                        else:
                            st.warning("No results found.")
                    else:
                        st.error(f"API Error: {response.text}")
                except Exception as e:
                    st.error("Could not connect to FastAPI server. Ensure it is running on http://127.0.0.1:8000.")
        else:
            st.warning("Please enter a query.")
