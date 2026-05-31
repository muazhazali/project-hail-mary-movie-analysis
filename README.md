# Movie Intelligence Platform

## Overview

A multimodal movie analytics platform that analyzes films using NLP, computer vision, and audience intelligence. Built as a portfolio project demonstrating modern AI/data engineering capabilities with a distinctive custom frontend.

### The Adaptation Arc

This platform analyzes **Project Hail Mary** and **The Martian** - two Andy Weir science fiction adaptations with different narrative patterns:
- **Project Hail Mary**: Discovery arc with oscillating sentiment
- **The Martian**: Survival arc with negative-to-positive build

## Quick Start

### Prerequisites

```bash
# Python 3.8+
# Node.js (optional, for future Next.js migration)
```

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd project-hail-mary-movie-analysis

# Install dependencies
pip install -r requirements.txt
# Or manually:
pip install fastapi uvicorn pydantic opencv-python
```

### Running the Application

#### Option 1: Quick Demo (Mock Data)

The frontend includes realistic mock data - no backend required for initial exploration.

```bash
# Serve the frontend
cd frontend
python3 -m http.server 8080

# Open browser
# http://localhost:8080/public/index.html
```

#### Option 2: Full Stack (API + Frontend)

**Terminal 1 - Start API:**
```bash
cd api
python3 main.py
# Or with auto-reload:
# uvicorn main:app --reload --port 8000
```

**Terminal 2 - Serve Frontend:**
```bash
cd frontend
python3 -m http.server 8080
```

**Open Browser:**
```
http://localhost:8080/public/index.html
```

## How to Use

### Dashboard Navigation

The application has three main tabs:

#### 1. Overview Tab
- **Metrics Panel**: Shows scenes count, average sentiment, dialogue scenes, protagonist
- **Timeline Scrubber**: 
  - Blue line = sentiment arc
  - Purple area = scene intensity
  - Colored dots = scenes (green=positive, red=negative, gray=neutral)
  - Click "Analyze" to play through the movie
  - Click anywhere on timeline to seek
  - Hover for timestamp
- **Character Network**: 
  - Click nodes to see relationships
  - Hover to highlight connections
  - Node size = screen time
- **Scene Explorer**: 
  - Filter by type (All/Dialogue/Action)
  - Search by character name
  - Click scene to jump to timestamp
- **Screen Time**: Character bars showing prominence

#### 2. Comparison Tab
- **The Adaptation Arc**: Compares two movies side-by-side
- **Metric Toggle**: Switch between Sentiment and Intensity
- **Act Markers**: Vertical lines showing Act 1 End, Midpoint, Act 2 End
- **Narrative Patterns**:
  - Hail Mary: Oscillating discovery arc
  - Martian: Building survival arc

#### 3. Audience Tab
- **Reddit Intelligence**: Top 5 most discussed scenes
  - Controversy score (higher = more divisive)
  - Mention counts
  - Character interactions
- **Sentiment Distribution**: Bar chart of emotional spread

### Video Processing (Optional)

To analyze your own movie:

```bash
# Process a video file
python src/video_pipeline.py --video /path/to/movie.mp4 --name "My Movie"

# Output: data/My Movie_video_metadata.json
#          data/frames/*.jpg (thumbnails and keyframes)
```

The pipeline will:
1. Detect scene cuts using frame differencing
2. Extract middle-frame thumbnails for each scene
3. Extract 3 keyframes per scene
4. Save metadata with timestamps

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/movies` | List available movies |
| `GET /api/movies/{id}/overview` | Movie statistics and characters |
| `GET /api/movies/{id}/timeline` | Scene data with sentiment |
| `GET /api/movies/{id}/network` | Character relationship graph |
| `GET /api/movies/{id}/scenes/{scene_id}` | Scene details |
| `POST /api/compare` | Compare multiple movies |
| `POST /api/search` | Semantic scene search |
| `GET /api/reddit/insights/{id}` | Reddit audience data |
| `GET /api/stats/{id}` | Statistical analysis |

Example API call:
```bash
curl http://localhost:8000/api/movies/hail_mary/timeline
```

## Architecture

```
Frontend (React + D3.js)  ←→  API (FastAPI)  ←→  Video Pipeline (OpenCV)
     ↓                           ↓                    ↓
  Timeline              Scene Data              Frame Extraction
  Network Graph         Character Analysis      Scene Detection
  Scene Explorer        Reddit Integration      Thumbnails
```

## Technology Stack

### Frontend
- React 18 (via CDN for rapid development)
- D3.js 7 (custom visualizations)
- Tailwind CSS (utility-first styling)
- Glassmorphism design system

### Backend
- FastAPI (high-performance Python API)
- Pydantic (data validation)
- Uvicorn (ASGI server)

### Video Processing
- OpenCV (computer vision)
- NumPy (numerical operations)
- Scene detection algorithms

## What Makes This Portfolio-Worthy

| Generic Portfolio | This Implementation |
|-------------------|---------------------|
| Streamlit dashboard | **Custom React + D3.js** |
| Pre-built chart libraries | **Hand-crafted visualizations** |
| Single movie analysis | **Multi-movie comparison** |
| Basic sentiment | **Reddit audience correlation** |
| Tutorial code | **Production architecture** |
| Generic theme | **Distinctive glassmorphism** |

### Key Differentiators

1. **"The Adaptation Arc"** - Specific narrative concept comparing Andy Weir adaptations
2. **Custom D3.js** - No chart libraries, hand-crafted timeline and network
3. **Video Pipeline** - Real scene detection and frame extraction
4. **Reddit Integration** - Audience sentiment correlation
5. **Glassmorphism Design** - Dark slate theme with blur effects

## Development

### Project Structure

```
├── api/
│   └── main.py              # FastAPI application
├── frontend/
│   ├── public/
│   │   └── index.html       # Entry point
│   └── src/
│       └── App.jsx          # React components
├── src/
│   ├── video_pipeline.py    # Scene detection
│   ├── nlp_analytics.py     # Text analysis
│   └── semantic_search.py   # Vector search
├── data/                    # Generated data and frames
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Adding New Movies

1. Add movie data to `api/main.py` in `generate_mock_movie_data()`:
```python
elif "my_movie" in movie_id.lower():
    title = "My Movie"
    duration = 7200
    characters = [...]
    # Define narrative pattern in scene generation
```

2. Restart API server
3. Select movie from dropdown

### Customizing Visualizations

The D3.js visualizations are in `frontend/src/App.jsx`:
- `TimelineScrubber`: Line/area charts with markers
- `CharacterConstellation`: Force-directed network
- `ComparisonView`: Multi-line normalized charts

## Troubleshooting

### Frontend not loading
```bash
# Check server is running
curl http://localhost:8080/public/index.html

# Try different port
python3 -m http.server 3000
```

### API errors
```bash
# Test API
curl http://localhost:8000/

# Check imports
cd api && python3 -c "from main import app; print('OK')"
```

### Video processing errors
```bash
# Install OpenCV
pip install opencv-python

# Verify installation
python3 -c "import cv2; print(cv2.__version__)"
```

## Future Enhancements

- [ ] PostgreSQL + pgvector for embeddings
- [ ] Real Reddit API integration (PRAW)
- [ ] Next.js migration with SSR
- [ ] WebSocket for real-time updates
- [ ] Trailer optimization analytics
- [ ] TV series support

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- Andy Weir for Project Hail Mary and The Martian
- D3.js community for visualization patterns
- FastAPI team for the excellent framework