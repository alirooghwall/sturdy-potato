"""Document embedding and similarity service using sentence transformers.

Provides semantic embeddings for text similarity, clustering, and search.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Document embedding service using sentence transformers.
    
    Features:
    - Semantic text embeddings
    - Similarity computation
    - Document clustering
    - Semantic search
    - Duplicate detection
    """

    def __init__(self, model_name: str = "embedding"):
        """Initialize embedding service.
        
        Args:
            model_name: Model to use (embedding, embedding_large)
        """
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        
        # Model registry
        self.models = {
            "embedding": "sentence-transformers/all-MiniLM-L6-v2",  # Fast, 384 dim
            "embedding_large": "sentence-transformers/all-mpnet-base-v2",  # Better quality, 768 dim
        }
        
        logger.info(f"Embedding service initialized with model: {model_name}")
    
    def _get_model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            model_id = self.models.get(self.model_name, self.model_name)
            logger.info(f"Loading embedding model: {model_id}")
            
            # Import here to avoid loading at module import
            from src.config.settings import get_settings
            settings = get_settings()
            
            cache_dir = getattr(settings, "model_cache_dir", "./models")
            
            self._model = SentenceTransformer(model_id, cache_folder=cache_dir)
            logger.info("✓ Embedding model loaded")
        
        return self._model
    
    def encode(
        self,
        texts: str | List[str],
        normalize: bool = True,
    ) -> np.ndarray:
        """Encode text(s) into embeddings.
        
        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize embeddings (recommended for similarity)
        
        Returns:
            Embeddings as numpy array
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        try:
            model = self._get_model()
            
            embeddings = model.encode(
                texts,
                normalize_embeddings=normalize,
                show_progress_bar=False,
            )
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            return np.array([])
    
    def similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """Compute semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        embeddings = self.encode([text1, text2])
        
        if len(embeddings) != 2:
            return 0.0
        
        # Cosine similarity
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        
        return float(similarity)
    
    def batch_similarity(
        self,
        texts1: List[str],
        texts2: List[str],
    ) -> np.ndarray:
        """Compute pairwise similarities between two lists of texts.
        
        Args:
            texts1: First list of texts
            texts2: Second list of texts
        
        Returns:
            Matrix of similarities (len(texts1) x len(texts2))
        """
        embeddings1 = self.encode(texts1)
        embeddings2 = self.encode(texts2)
        
        if len(embeddings1) == 0 or len(embeddings2) == 0:
            return np.array([])
        
        # Compute cosine similarity matrix
        similarities = util.cos_sim(embeddings1, embeddings2).numpy()
        
        return similarities
    
    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find most similar texts to a query.
        
        Args:
            query: Query text
            candidates: List of candidate texts
            top_k: Number of top results to return
        
        Returns:
            List of top matches with scores
        """
        if not candidates:
            return []
        
        # Encode query and candidates
        query_embedding = self.encode(query)
        candidate_embeddings = self.encode(candidates)
        
        # Compute similarities
        similarities = util.cos_sim(query_embedding, candidate_embeddings)[0]
        
        # Get top-k
        top_results = []
        for idx in similarities.argsort(descending=True)[:top_k]:
            top_results.append({
                "text": candidates[idx],
                "score": float(similarities[idx]),
                "index": int(idx),
            })
        
        return top_results
    
    def find_duplicates(
        self,
        texts: List[str],
        threshold: float = 0.85,
    ) -> List[Tuple[int, int, float]]:
        """Find duplicate or near-duplicate texts.
        
        Args:
            texts: List of texts
            threshold: Similarity threshold for duplicates (0-1)
        
        Returns:
            List of (index1, index2, similarity) tuples
        """
        if len(texts) < 2:
            return []
        
        # Encode all texts
        embeddings = self.encode(texts)
        
        # Compute pairwise similarities
        similarities = util.cos_sim(embeddings, embeddings)
        
        # Find pairs above threshold
        duplicates = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                sim = similarities[i][j].item()
                if sim >= threshold:
                    duplicates.append((i, j, float(sim)))
        
        # Sort by similarity (descending)
        duplicates.sort(key=lambda x: x[2], reverse=True)
        
        return duplicates
    
    def cluster_texts(
        self,
        texts: List[str],
        n_clusters: int = 5,
    ) -> List[int]:
        """Cluster texts based on semantic similarity.
        
        Args:
            texts: List of texts
            n_clusters: Number of clusters
        
        Returns:
            List of cluster assignments (one per text)
        """
        if len(texts) < n_clusters:
            return list(range(len(texts)))
        
        try:
            from sklearn.cluster import KMeans
            
            # Encode texts
            embeddings = self.encode(texts)
            
            # K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(embeddings)
            
            return clusters.tolist()
        
        except Exception as e:
            logger.error(f"Error clustering texts: {e}")
            return [0] * len(texts)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model.
        
        Returns:
            Embedding dimension
        """
        model = self._get_model()
        return model.get_sentence_embedding_dimension()
    
    def semantic_search(
        self,
        query: str,
        corpus: List[str],
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search over a corpus.
        
        Args:
            query: Search query
            corpus: List of documents to search
            top_k: Number of results
            score_threshold: Minimum similarity score
        
        Returns:
            List of search results with scores
        """
        results = self.find_most_similar(query, corpus, top_k)
        
        # Filter by threshold
        filtered = [r for r in results if r["score"] >= score_threshold]
        
        return filtered
    
    def compute_document_diversity(
        self,
        texts: List[str],
    ) -> Dict[str, float]:
        """Compute diversity metrics for a collection of texts.
        
        Args:
            texts: List of texts
        
        Returns:
            Dictionary with diversity metrics
        """
        if len(texts) < 2:
            return {
                "avg_similarity": 0.0,
                "diversity_score": 1.0,
            }
        
        # Encode all texts
        embeddings = self.encode(texts)
        
        # Compute pairwise similarities
        similarities = util.cos_sim(embeddings, embeddings)
        
        # Average similarity (excluding diagonal)
        n = len(texts)
        total_sim = 0.0
        count = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                total_sim += similarities[i][j].item()
                count += 1
        
        avg_similarity = total_sim / count if count > 0 else 0.0
        
        # Diversity is inverse of similarity
        diversity_score = 1.0 - avg_similarity
        
        return {
            "avg_similarity": float(avg_similarity),
            "diversity_score": float(diversity_score),
            "num_documents": n,
        }


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
