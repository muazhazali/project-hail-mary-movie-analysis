"""
Movie Intelligence Platform API
FastAPI backend for multimodal movie analytics
"""
import math
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import existing modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.nlp_analytics import NLPAnalytics, CharacterNetworkAnalyzer
except ImportError:
    # Fallback if imports fail
    NLPAnalytics = None
    CharacterNetworkAnalyzer = None

app = FastAPI(
    title="Movie Intelligence Platform",
    description="Multimodal analytics for film analysis",
    version="2.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data"
FRAMES_DIR = DATA_DIR / "frames"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory cache for processed data
data_cache = {}

# Pydantic models
class MovieOverview(BaseModel):
    id: str
    title: str
    duration: float
    total_scenes: int
    avg_sentiment: float
    characters: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]

class Scene(BaseModel):
    id: int
    start_time: float
    end_time: float
    sentiment: float
    intensity: float
    characters: List[str]
    dialogue_count: int
    type: str
    thumbnail_url: Optional[str] = None

class TimelineData(BaseModel):
    movie_id: str
    scenes: List[Scene]
    duration: float

class CharacterNode(BaseModel):
    id: str
    name: str
    color: str
    screen_time: float
    x: Optional[float] = None
    y: Optional[float] = None

class Relationship(BaseModel):
    source: str
    target: str
    strength: float
    type: str

class NetworkData(BaseModel):
    nodes: List[CharacterNode]
    links: List[Relationship]

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    scene_id: int
    start_time: float
    text: str
    similarity: float

class RedditInsight(BaseModel):
    scene_id: int
    timestamp: float
    controversy_score: float
    mentions: int
    top_comments: List[str]

class ComparisonRequest(BaseModel):
    movie_ids: List[str]
    metric: str = "sentiment"  # sentiment, intensity, dialogue

# Helper functions
def load_movie_data(movie_id: str) -> Dict:
    """Load processed movie data from cache or file"""
    if movie_id in data_cache:
        return data_cache[movie_id]
    
    # Try to load from file
    data_file = CACHE_DIR / f"{movie_id}_data.json"
    if data_file.exists():
        with open(data_file) as f:
            data = json.load(f)
            data_cache[movie_id] = data
            return data
    
    # Generate mock data if not found
    return generate_mock_movie_data(movie_id)

def generate_mock_movie_data(movie_id: str) -> Dict:
    """Generate realistic mock data for a movie"""
    movie_id_lower = movie_id.lower()
    is_hail_mary = "hail" in movie_id_lower or movie_id == "0" or movie_id == "hail_mary"
    is_martian = "martian" in movie_id_lower or movie_id == "1" or movie_id == "martian"
    
    if is_hail_mary:
        title = "Project Hail Mary"
        duration = 7800
        characters = [
            {"id": "grace", "name": "Grace", "color": "#60a5fa", "screen_time": 0.65},
            {"id": "rocky", "name": "Rocky", "color": "#a78bfa", "screen_time": 0.45},
            {"id": "stratt", "name": "Stratt", "color": "#f472b6", "screen_time": 0.25},
            {"id": "duy", "name": "Dr. Duy", "color": "#34d399", "screen_time": 0.15}
        ]
    elif is_martian:
        title = "The Martian"
        duration = 8100
        characters = [
            {"id": "watney", "name": "Watney", "color": "#f97316", "screen_time": 0.72},
            {"id": "nasa", "name": "NASA Team", "color": "#3b82f6", "screen_time": 0.38},
            {"id": "teddy", "name": "Teddy", "color": "#10b981", "screen_time": 0.22},
            {"id": "venkat", "name": "Venkat", "color": "#8b5cf6", "screen_time": 0.18}
        ]
    else:
        title = movie_id.replace("_", " ").title()
        duration = 7200
        characters = [
            {"id": "hero", "name": "Protagonist", "color": "#60a5fa", "screen_time": 0.6},
            {"id": "ally", "name": "Ally", "color": "#34d399", "screen_time": 0.35},
            {"id": "villain", "name": "Antagonist", "color": "#ef4444", "screen_time": 0.25}
        ]
    
    # Generate scenes with narrative arc
    num_scenes = 50
    scenes = []
    for i in range(num_scenes):
        progress = i / num_scenes
        
        # Different sentiment curves for different movies
        if is_martian:
            # Survival arc - starts negative, builds to positive
            base_sentiment = -0.4 + progress * 0.9
        else:
            # Discovery arc - peaks in middle
            base_sentiment = math.sin(progress * math.pi * 2) * 0.4
        
        sentiment = base_sentiment + (0.3 if i % 7 == 0 else 0) + (0.2 if i % 5 == 0 else 0)
        sentiment = max(-1, min(1, sentiment + (0.15 if i == num_scenes - 1 else 0)))
        
        scenes.append({
            "id": i,
            "start_time": i * (duration / num_scenes),
            "end_time": (i + 1) * (duration / num_scenes),
            "sentiment": sentiment,
            "intensity": 0.3 + (0.6 if abs(sentiment) > 0.5 else 0) + 0.1 * (i % 4),
            "characters": [c["name"] for c in characters[:2 if i % 3 == 0 else 1]],
            "dialogue_count": int(5 + 8 * (1 - abs(sentiment)) + 3 * (i % 4)),
            "type": "action" if i % 4 == 0 else "dialogue",
            "thumbnail_url": f"/api/frames/scene_{i:04d}.jpg"
        })
    
    return {
        "id": movie_id,
        "title": title,
        "duration": duration,
        "scenes": scenes,
        "characters": characters,
        "relationships": [
            {"source": characters[0]["id"], "target": characters[1]["id"], 
             "strength": 0.85, "type": "partnership"},
            {"source": characters[0]["id"], "target": characters[2]["id"], 
             "strength": 0.35, "type": "authority"},
            {"source": characters[1]["id"], "target": characters[2]["id"], 
             "strength": 0.15, "type": "distant"}
        ]
    }

# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "Movie Intelligence Platform",
        "version": "2.0.0",
        "endpoints": [
            "/api/movies",
            "/api/movies/{movie_id}/overview",
            "/api/movies/{movie_id}/timeline",
            "/api/movies/{movie_id}/network",
            "/api/movies/{movie_id}/scenes/{scene_id}",
            "/api/compare",
            "/api/search",
            "/api/reddit/insights/{movie_id}"
        ]
    }

@app.get("/api/movies")
async def list_movies() -> List[Dict[str, str]]:
    """List available movies"""
    return [
        {"id": "hail_mary", "title": "Project Hail Mary"},
        {"id": "martian", "title": "The Martian"},
        {"id": "interstellar", "title": "Interstellar"}
    ]

@app.get("/api/movies/{movie_id}/overview")
async def get_movie_overview(movie_id: str) -> Dict:
    """Get high-level overview of a movie"""
    data = load_movie_data(movie_id)
    
    avg_sentiment = sum(s["sentiment"] for s in data["scenes"]) / len(data["scenes"])
    
    return {
        "id": data["id"],
        "title": data["title"],
        "duration": data["duration"],
        "total_scenes": len(data["scenes"]),
        "avg_sentiment": avg_sentiment,
        "characters": data["characters"],
        "relationships": data["relationships"]
    }

@app.get("/api/movies/{movie_id}/timeline")
async def get_timeline(movie_id: str) -> TimelineData:
    """Get timeline data for sentiment/intensity visualization"""
    data = load_movie_data(movie_id)
    
    scenes = [
        Scene(
            id=s["id"],
            start_time=s["start_time"],
            end_time=s["end_time"],
            sentiment=s["sentiment"],
            intensity=s["intensity"],
            characters=s["characters"],
            dialogue_count=s["dialogue_count"],
            type=s["type"],
            thumbnail_url=s.get("thumbnail_url")
        )
        for s in data["scenes"]
    ]
    
    return TimelineData(
        movie_id=movie_id,
        scenes=scenes,
        duration=data["duration"]
    )

@app.get("/api/movies/{movie_id}/network")
async def get_network(movie_id: str) -> NetworkData:
    """Get character relationship network data"""
    data = load_movie_data(movie_id)
    
    # Calculate positions for force-directed layout
    nodes = []
    for i, char in enumerate(data["characters"]):
        angle = 2 * math.pi * i / len(data["characters"])
        radius = 100
        nodes.append(CharacterNode(
            id=char["id"],
            name=char["name"],
            color=char["color"],
            screen_time=char["screen_time"],
            x=200 + radius * (0.8 if i % 2 == 0 else -0.6),
            y=150 + radius * (0.6 if i < 2 else -0.8)
        ))
    
    links = [
        Relationship(
            source=r["source"],
            target=r["target"],
            strength=r["strength"],
            type=r["type"]
        )
        for r in data["relationships"]
    ]
    
    return NetworkData(nodes=nodes, links=links)

@app.get("/api/movies/{movie_id}/scenes/{scene_id}")
async def get_scene_detail(movie_id: str, scene_id: int) -> Dict:
    """Get detailed information about a specific scene"""
    data = load_movie_data(movie_id)
    
    scene = next((s for s in data["scenes"] if s["id"] == scene_id), None)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    return {
        **scene,
        "movie_title": data["title"],
        "dialogue_snippets": [
            f"Sample dialogue from scene {scene_id}...",
            f"Character interaction at {scene['start_time']}s"
        ]
    }

@app.get("/api/frames/{frame_name}")
async def get_frame(frame_name: str):
    """Serve frame/thumbnail images"""
    frame_path = FRAMES_DIR / frame_name
    if not frame_path.exists():
        # Return placeholder
        raise HTTPException(status_code=404, detail="Frame not found")
    
    return FileResponse(str(frame_path))

@app.post("/api/compare")
async def compare_movies(request: ComparisonRequest) -> List[Dict]:
    """Compare multiple movies on specified metrics"""
    movies = []
    
    for movie_id in request.movie_ids:
        data = load_movie_data(movie_id)
        
        # Calculate normalized scenes (0-1 progress)
        scenes = [
            {
                **s,
                "progress": i / len(data["scenes"])
            }
            for i, s in enumerate(data["scenes"])
        ]
        
        # Calculate average for the metric
        metric_values = [s[request.metric] for s in scenes]
        avg_value = sum(metric_values) / len(metric_values)
        
        movies.append({
            "title": data["title"],
            "duration": data["duration"],
            "scenes": scenes,
            "avg": avg_value
        })
    
    return movies

@app.post("/api/search")
async def semantic_search(query: SearchQuery) -> List[SearchResult]:
    """Semantic search over movie scenes"""
    # This would connect to pgvector in production
    # For now, return mock results
    return [
        SearchResult(
            scene_id=15,
            start_time=1200,
            text=f"Scene related to: {query.query}",
            similarity=0.89
        ),
        SearchResult(
            scene_id=23,
            start_time=1840,
            text=f"Another relevant scene for: {query.query}",
            similarity=0.82
        ),
        SearchResult(
            scene_id=8,
            start_time=650,
            text=f"Context for: {query.query}",
            similarity=0.75
        )
    ]

@app.get("/api/reddit/insights/{movie_id}")
async def get_reddit_insights(movie_id: str, limit: int = 5) -> List[RedditInsight]:
    """Get Reddit discussion insights for a movie"""
    data = load_movie_data(movie_id)
    
    # Simulate controversial scenes based on sentiment volatility
    scenes_with_scores = []
    for i, scene in enumerate(data["scenes"]):
        # Controversy = high sentiment change + high intensity
        prev_sentiment = data["scenes"][i-1]["sentiment"] if i > 0 else 0
        sentiment_change = abs(scene["sentiment"] - prev_sentiment)
        
        controversy = sentiment_change * scene["intensity"] * (0.5 + 0.5 * (scene["id"] % 100) / 100)
        
        scenes_with_scores.append({
            **scene,
            "controversy_score": min(1.0, controversy),
            "mentions": int(50 + controversy * 450)
        })
    
    # Sort by controversy and take top
    top_scenes = sorted(scenes_with_scores, key=lambda x: x["controversy_score"], reverse=True)[:limit]
    
    return [
        RedditInsight(
            scene_id=s["id"],
            timestamp=s["start_time"],
            controversy_score=s["controversy_score"],
            mentions=s["mentions"],
            top_comments=[
                f"This scene really got people talking...",
                f"The {s['characters'][0] if s['characters'] else 'protagonist'} moment was intense!",
                f"Controversial take: this was the best part"
            ]
        )
        for s in top_scenes
    ]

@app.get("/api/stats/{movie_id}")
async def get_statistics(movie_id: str) -> Dict:
    """Get statistical analysis of a movie"""
    data = load_movie_data(movie_id)
    scenes = data["scenes"]
    
    sentiments = [s["sentiment"] for s in scenes]
    intensities = [s["intensity"] for s in scenes]
    
    avg_sent = sum(sentiments) / len(sentiments)
    
    return {
        "total_scenes": len(scenes),
        "avg_sentiment": avg_sent,
        "sentiment_variance": sum((s - avg_sent)**2 for s in sentiments) / len(sentiments),
        "avg_intensity": sum(intensities) / len(intensities),
        "dialogue_heavy_scenes": len([s for s in scenes if s["dialogue_count"] > 10]),
        "action_scenes": len([s for s in scenes if s["type"] == "action"]),
        "peak_sentiment": max(sentiments),
        "lowest_sentiment": min(sentiments),
        "dominant_character": data["characters"][0]["name"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)