"""
NLP Analytics Module
Provides text analysis without heavy dependencies
"""
from typing import List, Dict, Any, Optional
import re
from collections import Counter
from dataclasses import dataclass

@dataclass
class SentimentResult:
    score: float  # -1 to 1
    magnitude: float
    label: str

@dataclass
class DialogueStats:
    total_words: int
    avg_words_per_line: float
    unique_words: int
    readability_score: float

class NLPAnalytics:
    """Lightweight NLP analytics without heavy dependencies"""
    
    def __init__(self):
        # Simple sentiment lexicon
        self.positive_words = set([
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'happy', 'joy', 'success', 'win', 'victory',
            'hope', 'believe', 'trust', 'friend', 'partner', 'help', 'save',
            'discover', 'learn', 'understand', 'yes', 'right', 'correct'
        ])
        
        self.negative_words = set([
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry',
            'sad', 'depressed', 'fear', 'scared', 'afraid', 'death', 'die', 'kill',
            'destroy', 'fail', 'failure', 'lose', 'loss', 'wrong', 'no', 'never',
            'alone', 'isolated', 'stranded', 'doomed', 'hopeless'
        ])
        
        self.intensifiers = set(['very', 'extremely', 'incredibly', 'absolutely', 'completely'])
        self.negations = set(['not', 'no', 'never', 'nothing', 'nobody', 'neither', 'nor'])
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of text using lexicon approach"""
        words = re.findall(r'\b\w+\b', text.lower())
        
        pos_count = sum(1 for w in words if w in self.positive_words)
        neg_count = sum(1 for w in words if w in self.negative_words)
        
        total = pos_count + neg_count
        if total == 0:
            return SentimentResult(score=0, magnitude=0.1, label="neutral")
        
        score = (pos_count - neg_count) / total
        magnitude = total / len(words) if words else 0
        
        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"
        
        return SentimentResult(score=score, magnitude=magnitude, label=label)
    
    def analyze_dialogue(self, text: str) -> DialogueStats:
        """Analyze dialogue complexity"""
        words = re.findall(r'\b\w+\b', text.lower())
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        
        unique_words = len(set(words))
        avg_words = len(words) / len(sentences) if sentences else 0
        
        # Simple readability: avg sentence length
        readability = max(0, min(100, 100 - (avg_words - 15) * 5))
        
        return DialogueStats(
            total_words=len(words),
            avg_words_per_line=avg_words,
            unique_words=unique_words,
            readability_score=readability
        )
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract character/entity mentions"""
        # Simple pattern: capitalized words
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(entities))[:10]
    
    def extract_topics(self, text: str, n_topics: int = 5) -> List[str]:
        """Extract key topics using simple frequency"""
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        
        # Filter common stop words
        stop_words = {'that', 'with', 'have', 'this', 'will', 'your', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'}
        words = [w for w in words if w not in stop_words]
        
        # Get top words
        counter = Counter(words)
        return [word for word, _ in counter.most_common(n_topics)]

# Simple semantic search using keyword matching
class SimpleSemanticSearch:
    def __init__(self):
        self.documents = []
    
    def add_document(self, doc_id: str, text: str, metadata: Dict):
        self.documents.append({
            'id': doc_id,
            'text': text,
            'metadata': metadata,
            'tokens': set(text.lower().split())
        })
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_tokens = set(query.lower().split())
        
        results = []
        for doc in self.documents:
            intersection = len(query_tokens & doc['tokens'])
            union = len(query_tokens | doc['tokens'])
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0:
                results.append({
                    'id': doc['id'],
                    'text': doc['text'][:200] + '...',
                    'similarity': similarity,
                    'metadata': doc['metadata']
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

# Character network analysis
class CharacterNetworkAnalyzer:
    def __init__(self):
        self.characters = {}
        self.interactions = []
    
    def add_character(self, char_id: str, name: str, **kwargs):
        self.characters[char_id] = {
            'id': char_id,
            'name': name,
            'mentions': 0,
            **kwargs
        }
    
    def record_interaction(self, char1: str, char2: str, weight: float = 1.0):
        self.interactions.append({
            'source': char1,
            'target': char2,
            'weight': weight
        })
        
        for char in [char1, char2]:
            if char in self.characters:
                self.characters[char]['mentions'] += weight
    
    def get_network_data(self) -> Dict:
        nodes = [
            {
                'id': cid,
                'name': data['name'],
                'size': 20 + data['mentions'] * 5
            }
            for cid, data in self.characters.items()
        ]
        
        return {
            'nodes': nodes,
            'links': self.interactions
        }

# Default instance
nlp = NLPAnalytics()