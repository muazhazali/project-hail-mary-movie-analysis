import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# ---------------------------------------------
# 1. Database Setup
# ---------------------------------------------
Base = declarative_base()

class SemanticScene(Base):
    __tablename__ = 'semantic_scenes'
    id = Column(Integer, primary_key=True)
    minute_window = Column(Integer)
    start_time_str = Column(String)
    text = Column(String)
    embedding = Column(Vector(384))

load_dotenv()
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_user = os.getenv("DB_USER", "postgres")
db_pass = os.getenv("DB_PASS", "postgres")
db_name = os.getenv("DB_NAME", "postgres")

connection_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
engine = create_engine(connection_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------
# 2. ML Model Management
# ---------------------------------------------
# We load the model on startup so it's ready in memory for fast API responses
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading SentenceTransformer model...")
    ml_models["encoder"] = SentenceTransformer('all-MiniLM-L6-v2')
    yield
    # Clean up on shutdown
    ml_models.clear()

# ---------------------------------------------
# 3. FastAPI App Initialization
# ---------------------------------------------
app = FastAPI(
    title="Movie Intelligence API",
    description="Semantic Search API for Project Hail Mary.",
    version="1.0.0",
    lifespan=lifespan
)

# Allow CORS for potential frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------
# 4. Endpoints
# ---------------------------------------------
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Movie Intelligence API is running."}

@app.get("/search")
def semantic_search(
    q: str = Query(..., description="The semantic search query"),
    top_k: int = Query(3, ge=1, le=20, description="Number of results to return")
):
    """
    Search for movie scenes based on semantic meaning.
    Example: /search?q=sacrifice and friendship
    """
    model = ml_models.get("encoder")
    if model is None:
        raise HTTPException(status_code=503, detail="ML model is currently loading. Try again in a few seconds.")
        
    # Generate embedding for the query
    query_embedding = model.encode(q)
    
    db = SessionLocal()
    try:
        # Perform vector similarity search
        results = db.query(SemanticScene).order_by(
            SemanticScene.embedding.cosine_distance(query_embedding)
        ).limit(top_k).all()
        
        response_data = []
        for res in results:
            # Calculate similarity score (cosine distance is 0 for identical, 2 for exactly opposite)
            # We convert it to a rough similarity percentage for the API response
            distance = res.embedding.cosine_distance(query_embedding)
            # Evaluate using SQLAlchemy to get the float value. Since we don't have the value natively extracted 
            # easily without a custom select, we just omit the exact score or return the object data.
            response_data.append({
                "minute": res.minute_window,
                "timestamp": res.start_time_str,
                "dialogue": res.text
            })
            
        return {"query": q, "results": response_data}
    finally:
        db.close()
