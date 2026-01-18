"""Model manager for loading, caching, and managing ML models.

Handles model lifecycle, GPU/CPU allocation, and caching.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    AutoModel,
    pipeline,
)

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages ML model loading, caching, and device allocation.
    
    Features:
    - Automatic GPU/CPU detection and allocation
    - Model caching to avoid reloading
    - Memory-efficient model management
    - Support for multiple model types
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        use_gpu: bool = True,
    ):
        """Initialize model manager.
        
        Args:
            cache_dir: Directory for model cache (default: ./models)
            use_gpu: Whether to use GPU if available
        """
        self.cache_dir = Path(cache_dir or "./models")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Device management
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device("cuda" if self.use_gpu else "cpu")
        
        if self.use_gpu:
            logger.info(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
            logger.info(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            logger.info("✓ Using CPU for inference")
        
        # Model cache
        self._models: Dict[str, Any] = {}
        self._tokenizers: Dict[str, Any] = {}
        self._pipelines: Dict[str, Any] = {}
        
        # Model registry
        self.models = {
            # Named Entity Recognition
            "ner": "dslim/bert-base-NER",
            "ner_large": "dbmdz/bert-large-cased-finetuned-conll03-english",
            
            # Sentiment Analysis
            "sentiment": "distilbert-base-uncased-finetuned-sst-2-english",
            "sentiment_roberta": "cardiffnlp/twitter-roberta-base-sentiment-latest",
            
            # Zero-shot Classification
            "zero_shot": "facebook/bart-large-mnli",
            
            # Text Embedding
            "embedding": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_large": "sentence-transformers/all-mpnet-base-v2",
            
            # Multilingual (for Pashto, Dari support in future)
            "multilingual_ner": "Davlan/xlm-roberta-base-ner-hrl",
            "multilingual_sentiment": "nlptown/bert-base-multilingual-uncased-sentiment",
        }
        
        logger.info(f"✓ Model manager initialized (device: {self.device})")
    
    def load_model(
        self,
        model_name: str,
        model_type: str = "sequence_classification",
    ) -> Any:
        """Load a model and cache it.
        
        Args:
            model_name: Model identifier (from registry or HuggingFace)
            model_type: Type of model (sequence_classification, token_classification, etc.)
        
        Returns:
            Loaded model
        """
        # Resolve model name from registry
        model_id = self.models.get(model_name, model_name)
        
        # Check cache
        cache_key = f"{model_id}_{model_type}"
        if cache_key in self._models:
            logger.debug(f"Using cached model: {model_name}")
            return self._models[cache_key]
        
        logger.info(f"Loading model: {model_name} ({model_id})")
        
        try:
            # Load based on type
            if model_type == "sequence_classification":
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_id,
                    cache_dir=str(self.cache_dir),
                )
            elif model_type == "token_classification":
                model = AutoModelForTokenClassification.from_pretrained(
                    model_id,
                    cache_dir=str(self.cache_dir),
                )
            elif model_type == "base":
                model = AutoModel.from_pretrained(
                    model_id,
                    cache_dir=str(self.cache_dir),
                )
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Move to device
            model = model.to(self.device)
            model.eval()  # Set to evaluation mode
            
            # Cache
            self._models[cache_key] = model
            
            logger.info(f"✓ Model loaded: {model_name}")
            return model
        
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def load_tokenizer(self, model_name: str) -> Any:
        """Load a tokenizer and cache it.
        
        Args:
            model_name: Model identifier
        
        Returns:
            Loaded tokenizer
        """
        # Resolve model name
        model_id = self.models.get(model_name, model_name)
        
        # Check cache
        if model_id in self._tokenizers:
            return self._tokenizers[model_id]
        
        logger.info(f"Loading tokenizer: {model_name}")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=str(self.cache_dir),
            )
            
            self._tokenizers[model_id] = tokenizer
            return tokenizer
        
        except Exception as e:
            logger.error(f"Failed to load tokenizer {model_name}: {e}")
            raise
    
    def create_pipeline(
        self,
        task: str,
        model_name: str,
        **kwargs,
    ) -> Any:
        """Create a HuggingFace pipeline.
        
        Args:
            task: Pipeline task (ner, sentiment-analysis, etc.)
            model_name: Model to use
            **kwargs: Additional pipeline arguments
        
        Returns:
            Pipeline instance
        """
        # Resolve model name
        model_id = self.models.get(model_name, model_name)
        
        # Check cache
        cache_key = f"{task}_{model_id}"
        if cache_key in self._pipelines:
            return self._pipelines[cache_key]
        
        logger.info(f"Creating pipeline: {task} with {model_name}")
        
        try:
            pipe = pipeline(
                task,
                model=model_id,
                tokenizer=model_id,
                device=0 if self.use_gpu else -1,
                model_kwargs={"cache_dir": str(self.cache_dir)},
                **kwargs,
            )
            
            self._pipelines[cache_key] = pipe
            logger.info(f"✓ Pipeline created: {task}")
            return pipe
        
        except Exception as e:
            logger.error(f"Failed to create pipeline {task}: {e}")
            raise
    
    def unload_model(self, model_name: str) -> None:
        """Unload a model from cache to free memory.
        
        Args:
            model_name: Model to unload
        """
        model_id = self.models.get(model_name, model_name)
        
        # Remove from caches
        keys_to_remove = [k for k in self._models.keys() if model_id in k]
        for key in keys_to_remove:
            del self._models[key]
        
        if model_id in self._tokenizers:
            del self._tokenizers[model_id]
        
        keys_to_remove = [k for k in self._pipelines.keys() if model_id in k]
        for key in keys_to_remove:
            del self._pipelines[key]
        
        # Clear GPU cache if using GPU
        if self.use_gpu:
            torch.cuda.empty_cache()
        
        logger.info(f"✓ Model unloaded: {model_name}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics.
        
        Returns:
            Dictionary with memory stats
        """
        stats = {
            "device": str(self.device),
            "models_loaded": len(self._models),
            "tokenizers_loaded": len(self._tokenizers),
            "pipelines_loaded": len(self._pipelines),
        }
        
        if self.use_gpu:
            stats["gpu_memory_allocated"] = torch.cuda.memory_allocated() / 1e9  # GB
            stats["gpu_memory_reserved"] = torch.cuda.memory_reserved() / 1e9  # GB
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear all cached models and free memory."""
        logger.info("Clearing model cache...")
        
        self._models.clear()
        self._tokenizers.clear()
        self._pipelines.clear()
        
        if self.use_gpu:
            torch.cuda.empty_cache()
        
        logger.info("✓ Model cache cleared")


# Global instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        from src.config.settings import get_settings
        settings = get_settings()
        _model_manager = ModelManager(
            cache_dir=getattr(settings, "model_cache_dir", "./models"),
            use_gpu=getattr(settings, "enable_gpu", False),
        )
    return _model_manager
