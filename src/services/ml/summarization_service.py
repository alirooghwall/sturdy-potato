"""Text summarization service using transformers.

Generates concise summaries of long documents.
"""

import logging
from typing import Any, Dict, List, Optional

from .model_manager import get_model_manager

logger = logging.getLogger(__name__)


class SummarizationService:
    """Text summarization service.
    
    Provides:
    - Abstractive summarization (generate new text)
    - Extractive summarization (select key sentences)
    - Configurable length
    - Batch processing
    """

    def __init__(self, model_name: str = "summarization"):
        """Initialize summarization service.
        
        Args:
            model_name: Model to use (summarization, summarization_long)
        """
        self.model_name = model_name
        self.model_manager = get_model_manager()
        self._pipeline = None
        
        # Add models to registry if not present
        if "summarization" not in self.model_manager.models:
            self.model_manager.models["summarization"] = "facebook/bart-large-cnn"
            self.model_manager.models["summarization_long"] = "google/pegasus-xsum"
        
        logger.info(f"Summarization service initialized with model: {model_name}")
    
    def _get_pipeline(self):
        """Lazy load the summarization pipeline."""
        if self._pipeline is None:
            logger.info("Loading summarization pipeline...")
            self._pipeline = self.model_manager.create_pipeline(
                "summarization",
                self.model_name,
            )
            logger.info("✓ Summarization pipeline loaded")
        return self._pipeline
    
    def summarize(
        self,
        text: str,
        max_length: int = 130,
        min_length: int = 30,
        do_sample: bool = False,
    ) -> Dict[str, Any]:
        """Generate summary of text.
        
        Args:
            text: Input text to summarize
            max_length: Maximum summary length in tokens
            min_length: Minimum summary length in tokens
            do_sample: Whether to use sampling (more creative but less consistent)
        
        Returns:
            Dictionary with summary and metadata
        """
        if not text or not text.strip():
            return {
                "summary": "",
                "original_length": 0,
                "summary_length": 0,
                "compression_ratio": 0.0,
            }
        
        try:
            pipeline = self._get_pipeline()
            
            # Truncate if too long (model max is usually 1024 tokens)
            max_input = 1024
            text_truncated = text[:max_input * 4]  # Rough estimate: 4 chars per token
            
            # Generate summary
            result = pipeline(
                text_truncated,
                max_length=max_length,
                min_length=min_length,
                do_sample=do_sample,
                truncation=True,
            )[0]
            
            summary_text = result["summary_text"]
            
            return {
                "summary": summary_text,
                "original_length": len(text.split()),
                "summary_length": len(summary_text.split()),
                "compression_ratio": len(summary_text) / len(text) if text else 0.0,
                "truncated": len(text) > max_input * 4,
            }
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "summary": "",
                "original_length": len(text.split()),
                "summary_length": 0,
                "compression_ratio": 0.0,
                "error": str(e),
            }
    
    def summarize_batch(
        self,
        texts: List[str],
        max_length: int = 130,
        min_length: int = 30,
    ) -> List[Dict[str, Any]]:
        """Summarize multiple texts.
        
        Args:
            texts: List of texts to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length
        
        Returns:
            List of summary results
        """
        return [
            self.summarize(text, max_length, min_length)
            for text in texts
        ]
    
    def extractive_summary(
        self,
        text: str,
        num_sentences: int = 3,
    ) -> Dict[str, Any]:
        """Generate extractive summary by selecting key sentences.
        
        Args:
            text: Input text
            num_sentences: Number of sentences to extract
        
        Returns:
            Dictionary with extracted sentences
        """
        try:
            from src.services.ml import get_embedding_service
            import re
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= num_sentences:
                return {
                    "summary": text,
                    "sentences": sentences,
                    "method": "extractive",
                }
            
            # Use embeddings to find most representative sentences
            embeddings_service = get_embedding_service()
            
            # Embed all sentences
            sentence_embeddings = embeddings_service.encode(sentences)
            
            # Compute similarity to full document
            doc_embedding = embeddings_service.encode(text)
            
            from sentence_transformers import util
            similarities = util.cos_sim(sentence_embeddings, doc_embedding)
            
            # Get top sentences
            top_indices = similarities.squeeze().argsort(descending=True)[:num_sentences]
            top_indices = sorted(top_indices.tolist())  # Sort by position
            
            selected_sentences = [sentences[i] for i in top_indices]
            summary = '. '.join(selected_sentences) + '.'
            
            return {
                "summary": summary,
                "sentences": selected_sentences,
                "method": "extractive",
                "num_sentences": len(selected_sentences),
            }
        
        except Exception as e:
            logger.error(f"Error in extractive summary: {e}")
            # Fallback: just take first N sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            selected = sentences[:num_sentences]
            return {
                "summary": '. '.join(selected) + '.',
                "sentences": selected,
                "method": "extractive_fallback",
            }
    
    def summarize_news_article(
        self,
        title: str,
        content: str,
        max_length: int = 100,
    ) -> Dict[str, Any]:
        """Summarize a news article with title.
        
        Args:
            title: Article title
            content: Article content
            max_length: Maximum summary length
        
        Returns:
            Summary with title context
        """
        # Combine title and content with emphasis on title
        full_text = f"{title}. {content}"
        
        summary = self.summarize(full_text, max_length=max_length)
        summary["title"] = title
        
        return summary
    
    def generate_headlines(
        self,
        text: str,
        num_headlines: int = 3,
    ) -> List[str]:
        """Generate headline suggestions for text.
        
        Args:
            text: Input text
            num_headlines: Number of headlines to generate
        
        Returns:
            List of headline suggestions
        """
        try:
            # Generate very short summaries as headlines
            headlines = []
            
            for _ in range(num_headlines):
                summary = self.summarize(
                    text,
                    max_length=15,
                    min_length=5,
                    do_sample=True,  # Add variety
                )
                
                headline = summary["summary"]
                if headline and headline not in headlines:
                    headlines.append(headline)
            
            return headlines
        
        except Exception as e:
            logger.error(f"Error generating headlines: {e}")
            return []


# Global instance
_summarization_service: Optional[SummarizationService] = None


def get_summarization_service() -> SummarizationService:
    """Get the global summarization service instance."""
    global _summarization_service
    if _summarization_service is None:
        _summarization_service = SummarizationService()
    return _summarization_service
