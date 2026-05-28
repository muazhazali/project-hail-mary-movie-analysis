import os
import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
import warnings

warnings.filterwarnings('ignore')

Base = declarative_base()

class SemanticScene(Base):
    __tablename__ = 'semantic_scenes'
    id = Column(Integer, primary_key=True)
    minute_window = Column(Integer)
    start_time_str = Column(String)
    text = Column(String)
    embedding = Column(Vector(384))  # all-MiniLM-L6-v2 produces 384-dimensional embeddings

def time_to_seconds(t_str):
    try:
        h, m, s = t_str.split(':')
        s, ms = s.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + float(ms) / 1000.0
    except:
        return 0

def seconds_to_str(total_sec):
    h = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = int(total_sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def perform_search(session, query, model, top_k=3):
    print(f"\n--- SEMANTIC SEARCH ---")
    print(f"Query: '{query}'\n")
    
    # 1. Embed the query
    query_embedding = model.encode(query)
    
    # 2. Perform vector similarity search (cosine distance)
    # pgvector operator <=> represents cosine distance
    results = session.query(SemanticScene).order_by(
        SemanticScene.embedding.cosine_distance(query_embedding)
    ).limit(top_k).all()
    
    for i, res in enumerate(results, 1):
        print(f"Result #{i} | Time: {res.start_time_str}")
        print(f"Dialogue snippet:\n{res.text}\n")

def main():
    # 1. Setup & Data Loading
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_dir, 'outputs', 'subtitles.csv')
    
    print("Loading subtitle data...")
    df = pd.read_csv(data_path)
    df['time_sec'] = df['start_time'].apply(time_to_seconds)
    
    # Chunking into 1-minute scenes
    window_size = 60
    df['window_1min'] = df['time_sec'] // window_size
    
    print("Chunking dialogue into 1-minute scenes...")
    scenes = df.groupby('window_1min').agg({
        'text': lambda x: " ".join(x.fillna("").tolist()),
        'time_sec': 'min'
    }).reset_index()
    scenes['start_time_str'] = scenes['time_sec'].apply(seconds_to_str)
    
    # Remove empty scenes
    scenes = scenes[scenes['text'].str.strip().str.len() > 0]
    print(f"Total scenes to index: {len(scenes)}")
    
    # 2. Embedding Generation
    print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Encoding scenes into vector embeddings (this might take a moment)...")
    embeddings = model.encode(scenes['text'].tolist())
    
    # 3. Database Connection
    load_dotenv()
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASS", "postgres")
    db_name = os.getenv("DB_NAME", "postgres")
    
    connection_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    print(f"Connecting to database {db_host}...")
    
    engine = create_engine(connection_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Enable pgvector
    try:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()
    except Exception as e:
        print("Warning: Could not create extension 'vector'. It may already exist or there are permission issues.")
        print(e)
        session.rollback()
        
    print("Creating schema for semantic_scenes...")
    Base.metadata.drop_all(engine)  # Reset for this run
    Base.metadata.create_all(engine)
    
    # 4. Upload Data
    print("Uploading embeddings to PostgreSQL pgvector...")
    scene_objects = []
    for i, row in scenes.iterrows():
        scene_objects.append(
            SemanticScene(
                minute_window=row['window_1min'],
                start_time_str=row['start_time_str'],
                text=row['text'],
                embedding=embeddings[i]
            )
        )
        
    session.bulk_save_objects(scene_objects)
    session.commit()
    print("Upload complete!")
    
    # 5. Run a test semantic search
    test_query = "sacrifice and friendship"
    perform_search(session, test_query, model, top_k=3)

if __name__ == "__main__":
    main()
