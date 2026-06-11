"""Qdrant vector database service using REST API directly.

This module provides a REST-based implementation for Qdrant operations,
which works more reliably with cloud Qdrant instances that may have
timeout issues with the official Python client.
"""
import os
from typing import Optional
import requests
from app.config import get_settings


class QdrantRestClient:
    """Simple REST client for Qdrant API."""
    
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.qdrant_effective_url or f"http://{settings.qdrant_host}:{settings.qdrant_port}"
        self.api_key = settings.qdrant_api_key
        self.collection = settings.qdrant_collection
        self.vector_size = settings.qdrant_vector_size
        
        self.headers = {}
        if self.api_key:
            self.headers['api-key'] = self.api_key
    
    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make HTTP request to Qdrant API."""
        url = f"{self.base_url}{endpoint}"
        headers = {**self.headers, **kwargs.pop('headers', {})}
        
        # Disable SSL verification for development (optional)
        kwargs['verify'] = kwargs.get('verify', True)
        
        response = requests.request(
            method, url, headers=headers, timeout=30, **kwargs
        )
        response.raise_for_status()
        return response.json() if response.content else {}
    
    def get_collection(self, name: str) -> Optional[dict]:
        """Get collection info."""
        try:
            result = self._request('GET', f'/collections/{name}')
            return result.get('result')
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def create_collection(self, name: str, size: int, distance: str = "Cosine") -> bool:
        """Create a new collection."""
        payload = {
            "vectors": {
                "size": size,
                "distance": distance
            }
        }
        result = self._request('PUT', f'/collections/{name}', json=payload)
        return result.get('result', False)
    
    def upsert_points(self, name: str, points: list[dict]) -> bool:
        """Upsert points into collection."""
        payload = {"points": points}
        result = self._request('PUT', f'/collections/{name}/points', json=payload)
        return result.get('status') == 'ok'
    
    def search_points(self, name: str, vector: list[float], limit: int = 10, 
                     filter_: Optional[dict] = None) -> list[dict]:
        """Search for similar vectors."""
        payload = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
            "with_vector": False
        }
        if filter_:
            payload["filter"] = filter_
        
        result = self._request('POST', f'/collections/{name}/points/search', json=payload)
        return result.get('result', [])
    
    def count_points(self, name: str) -> int:
        """Get number of points in collection."""
        try:
            result = self._request('GET', f'/collections/{name}')
            return result.get('result', {}).get('points_count', 0)
        except:
            return 0


# Global client instance
_rest_client: Optional[QdrantRestClient] = None


def _get_rest_client() -> QdrantRestClient:
    """Get or create REST client."""
    global _rest_client
    if _rest_client is None:
        _rest_client = QdrantRestClient()
    return _rest_client


def get_qdrant_client():
    """Return REST client (compatible interface)."""
    return _get_rest_client()


def ensure_collection() -> None:
    """Ensure Qdrant collection exists."""
    client = _get_rest_client()
    collection = client.get_collection(client.collection)
    if collection is None:
        client.create_collection(client.collection, client.vector_size)


def upsert_embeddings(
    ids: list[int],
    embeddings: list[list[float]],
    payloads: list[dict],
) -> None:
    """Upsert embeddings with their metadata into Qdrant."""
    client = _get_rest_client()
    ensure_collection()
    
    points = [
        {
            "id": id_,
            "vector": embedding,
            "payload": payload
        }
        for id_, embedding, payload in zip(ids, embeddings, payloads)
    ]
    
    client.upsert_points(client.collection, points)


def search_similar(
    query_vector: list[float],
    limit: int = 10,
    speaker: Optional[str] = None,
) -> list[dict]:
    """Search for similar vectors in Qdrant."""
    client = _get_rest_client()
    
    # Build filter if speaker provided
    filter_ = None
    if speaker:
        filter_ = {
            "must": [
                {
                    "key": "speaker",
                    "match": {"value": speaker}
                }
            ]
        }
    
    results = client.search_points(
        client.collection,
        query_vector,
        limit=limit,
        filter_=filter_
    )
    
    return [
        {
            "id": r["id"],
            "score": r["score"],
            "payload": r.get("payload", {}),
        }
        for r in results
    ]


def delete_by_ids(ids: list[int]) -> None:
    """Delete points by IDs."""
    client = _get_rest_client()
    # Qdrant REST API for delete: POST /collections/{collection_name}/points/delete
    payload = {"points": ids}
    client._request('POST', f'/collections/{client.collection}/points/delete', json=payload)


def collection_exists() -> bool:
    """Check if the collection exists."""
    client = _get_rest_client()
    return client.get_collection(client.collection) is not None


def count_points() -> int:
    """Get the count of points in the collection."""
    client = _get_rest_client()
    return client.count_points(client.collection)
