# Machine Learning Integration Guide

## Overview

The ISR Platform now includes state-of-the-art ML capabilities using transformers and deep learning models. This guide covers all ML features, usage, and configuration.

---

## 🎯 ML Capabilities

### 1. Named Entity Recognition (NER)
**Model:** `dslim/bert-base-NER` (transformer-based)

**Extracts:**
- **PERSON** - People names
- **ORGANIZATION** - Companies, agencies, groups
- **LOCATION** - Cities, countries, regions
- **GPE** - Geopolitical entities
- **MISC** - Other named entities

**Example:**
```python
from src.services.ml import get_ner_service

ner = get_ner_service()
entities = ner.extract_entities("Taliban forces entered Kabul yesterday.")
# Returns: [
#   {"entity_type": "ORGANIZATION", "text": "Taliban", "confidence": 0.95},
#   {"entity_type": "LOCATION", "text": "Kabul", "confidence": 0.98}
# ]
```

### 2. Sentiment Analysis
**Model:** `distilbert-base-uncased-finetuned-sst-2-english`

**Detects:**
- Positive sentiment
- Negative sentiment
- Neutral sentiment
- Confidence scores

**Example:**
```python
from src.services.ml import get_sentiment_service

sentiment = get_sentiment_service()
result = sentiment.analyze("Peace talks are progressing well.")
# Returns: {"sentiment": "positive", "score": 0.92}
```

### 3. Zero-Shot Classification
**Model:** `facebook/bart-large-mnli`

**Features:**
- Custom label classification (no training needed)
- Multi-label support
- ISR topic categorization
- Threat level classification

**Example:**
```python
from src.services.ml import get_classification_service

classifier = get_classification_service()

# ISR topic classification
topics = classifier.classify_isr_topic("Military convoy attacked near border")
# Returns: [
#   {"category": "security threat", "score": 0.89},
#   {"category": "military operations", "score": 0.78}
# ]

# Custom labels (zero-shot)
result = classifier.classify(
    "Aid distribution in refugee camp",
    ["humanitarian", "military", "economic", "political"]
)
```

### 4. Threat Detection (Ensemble)
**Combines multiple models + rule-based**

**Analyzes:**
- Threat keywords (pattern matching)
- Negative sentiment
- Threat entity recognition
- Zero-shot threat classification

**Outputs:**
- Threat score (0-1)
- Threat level (none/low/medium/high/critical)
- Detailed analysis breakdown

**Example:**
```python
from src.services.ml import get_threat_detection_service

threat = get_threat_detection_service()
result = threat.detect_threats("IED attack reported in Kandahar")
# Returns: {
#   "threat_detected": True,
#   "threat_score": 0.85,
#   "threat_level": "high",
#   "details": {...}
# }
```

### 5. Semantic Embeddings & Similarity
**Model:** `sentence-transformers/all-MiniLM-L6-v2`

**Features:**
- Text embeddings (384 dimensions)
- Semantic similarity
- Duplicate detection
- Semantic search
- Document clustering

**Example:**
```python
from src.services.ml import get_embedding_service

embeddings = get_embedding_service()

# Similarity
sim = embeddings.similarity(
    "Military operation in Helmand",
    "Armed forces deploy to Helmand province"
)
# Returns: 0.87 (high similarity)

# Semantic search
results = embeddings.semantic_search(
    query="Taliban activity",
    corpus=news_articles,
    top_k=5
)

# Find duplicates
dupes = embeddings.find_duplicates(articles, threshold=0.85)
```

---

## 🚀 Quick Start

### Installation

```bash
# Install ML dependencies
pip install torch transformers sentence-transformers accelerate scikit-learn spacy nltk

# Or use requirements.txt
pip install -r requirements.txt
```

### Configuration

```bash
# .env file
MODEL_CACHE_DIR=./models
ENABLE_GPU=false  # Set to true if you have CUDA GPU
USE_ML_PROCESSING=true
```

### Basic Usage

```python
# Import ML services
from src.services.ml import (
    get_ner_service,
    get_sentiment_service,
    get_classification_service,
    get_threat_detection_service,
    get_embedding_service,
)

# Use services
ner = get_ner_service()
sentiment = get_sentiment_service()
classifier = get_classification_service()
threat = get_threat_detection_service()
embeddings = get_embedding_service()
```

---

## 📡 REST API Endpoints

All ML features are accessible via REST API at `/api/v1/ml-api`:

### Named Entity Recognition

```bash
# Extract all entities
POST /api/v1/ml-api/ner/extract
{
  "text": "Taliban forces in Kabul",
  "min_confidence": 0.5
}

# Extract locations only
POST /api/v1/ml-api/ner/locations
{"text": "Fighting in Kandahar and Helmand"}

# Extract organizations only
POST /api/v1/ml-api/ner/organizations
{"text": "UN and Red Cross operations"}
```

### Sentiment Analysis

```bash
# Single text
POST /api/v1/ml-api/sentiment/analyze
{"text": "Peace agreement signed"}

# Batch processing
POST /api/v1/ml-api/sentiment/batch
{"texts": ["text1", "text2", "text3"]}

# Statistics
POST /api/v1/ml-api/sentiment/statistics
{"texts": [...]}
```

### Classification

```bash
# Zero-shot classification
POST /api/v1/ml-api/classify
{
  "text": "Border security increased",
  "labels": ["security", "economic", "humanitarian"],
  "multi_label": false
}

# ISR topic classification
POST /api/v1/ml-api/classify/isr-topic
{"text": "IED discovered near checkpoint"}

# Threat level
POST /api/v1/ml-api/classify/threat-level
{"text": "Militants planning attack"}

# Afghanistan relevance
POST /api/v1/ml-api/classify/afghanistan-relevance
{"text": "News article text...", "threshold": 0.5}
```

### Threat Detection

```bash
# Detect threats
POST /api/v1/ml-api/threat/detect
{
  "text": "Bomb threat at embassy",
  "include_details": true
}

# Batch detection
POST /api/v1/ml-api/threat/batch
{"texts": [...], "include_details": false}

# Threat summary
POST /api/v1/ml-api/threat/summary
{"texts": [...]}
```

### Embeddings & Similarity

```bash
# Compute similarity
POST /api/v1/ml-api/similarity
{"text1": "...", "text2": "..."}

# Semantic search
POST /api/v1/ml-api/search
{
  "query": "Taliban operations",
  "documents": [...],
  "top_k": 5
}

# Find duplicates
POST /api/v1/ml-api/duplicates
{"texts": [...], "threshold": 0.85}
```

### Model Management

```bash
# Get model status
GET /api/v1/ml-api/models/status

# Get model registry
GET /api/v1/ml-api/models/registry

# Clear cache
POST /api/v1/ml-api/models/clear-cache
```

---

## 🔧 Stream Processing Integration

ML models are automatically integrated into the stream processing pipeline:

```python
from src.services.stream_processor import get_stream_processor

# Enable ML processing
processor = get_stream_processor()
# ML is enabled by default, use use_ml=False to disable

# Processes:
# - News articles → NER + sentiment + threat + topics
# - Social media → sentiment + bot detection + coordination
# - Sensor data → anomaly detection
```

**Enriched Data Example:**
```json
{
  "content": "Taliban forces entered Kabul",
  "ml_powered": true,
  "entities": {
    "all": [...],
    "locations": ["Kabul"],
    "organizations": ["Taliban"],
    "persons": []
  },
  "sentiment": "negative",
  "threat_analysis": {
    "threat_detected": true,
    "threat_score": 0.75,
    "threat_level": "high"
  },
  "topics": [
    {"category": "security threat", "score": 0.89},
    {"category": "military operations", "score": 0.76}
  ]
}
```

---

## 🎯 Model Registry

All available models:

| Model Name | Purpose | Size | Performance |
|------------|---------|------|-------------|
| `ner` | Named Entity Recognition | 110M | Fast, good accuracy |
| `ner_large` | NER (better quality) | 340M | Slower, higher accuracy |
| `sentiment` | Sentiment Analysis | 67M | Very fast |
| `sentiment_roberta` | Sentiment (better) | 125M | Slower, more accurate |
| `zero_shot` | Classification | 400M | Flexible, no training |
| `embedding` | Text Embeddings | 22M | Fast, 384 dims |
| `embedding_large` | Embeddings (better) | 110M | Better quality, 768 dims |
| `multilingual_ner` | Multilingual NER | 280M | For Pashto/Dari future support |

---

## ⚙️ Configuration

### GPU Support

```bash
# Enable GPU (requires CUDA)
ENABLE_GPU=true

# Check GPU availability
curl http://localhost:8000/api/v1/ml-api/models/status
```

### Model Caching

Models are cached in `MODEL_CACHE_DIR` (default: `./models`):

```
./models/
├── models--dslim--bert-base-NER/
├── models--distilbert-base-uncased-finetuned-sst-2-english/
├── models--facebook--bart-large-mnli/
└── sentence-transformers_all-MiniLM-L6-v2/
```

### Memory Management

```python
from src.services.ml import get_model_manager

manager = get_model_manager()

# Check memory usage
memory = manager.get_memory_usage()
print(f"Models loaded: {memory['models_loaded']}")
print(f"GPU memory: {memory.get('gpu_memory_allocated', 0)} GB")

# Clear cache to free memory
manager.clear_cache()
```

---

## 🔬 Advanced Usage

### Custom Models

```python
from src.services.ml import get_model_manager

manager = get_model_manager()

# Load custom model from HuggingFace
custom_model = manager.load_model("your-username/your-model", "sequence_classification")

# Create custom pipeline
pipeline = manager.create_pipeline("text-classification", "your-username/your-model")
```

### Batch Processing

```python
# Efficient batch processing
texts = ["text1", "text2", "text3", ...]

# Sentiment (batched)
sentiment_results = sentiment_service.analyze_batch(texts)

# Threat detection (batched)
threat_results = threat_service.batch_detect(texts)

# Classification (batched)
classification_results = classifier.batch_classify(texts, labels)
```

### Combining Multiple Services

```python
def comprehensive_analysis(text):
    """Comprehensive ML analysis."""
    # Extract entities
    entities = ner_service.extract_entities(text)
    
    # Analyze sentiment
    sentiment = sentiment_service.analyze(text)
    
    # Classify topics
    topics = classifier.classify_isr_topic(text)
    
    # Detect threats
    threats = threat_service.detect_threats(text)
    
    # Compute embedding
    embedding = embeddings_service.encode(text)
    
    return {
        "entities": entities,
        "sentiment": sentiment,
        "topics": topics,
        "threats": threats,
        "embedding": embedding.tolist(),
    }
```

---

## 📊 Performance Considerations

### CPU vs GPU

| Operation | CPU (i7) | GPU (RTX 3070) |
|-----------|----------|----------------|
| NER (single) | ~200ms | ~50ms |
| Sentiment (single) | ~150ms | ~30ms |
| Classification (single) | ~400ms | ~100ms |
| Embedding (single) | ~50ms | ~20ms |
| Batch (100 texts) | ~10s | ~2s |

### Optimization Tips

1. **Use Batching:** Process multiple texts together
2. **Enable GPU:** 4-5x speedup with CUDA
3. **Model Selection:** Use smaller models for speed
4. **Caching:** Models are cached after first load
5. **Async Processing:** Use stream processor for async

---

## 🐛 Troubleshooting

### Common Issues

**1. Models not loading:**
```bash
# Check network connection
# Models download from HuggingFace on first use
# Can take 5-30 minutes depending on model size
```

**2. Out of memory:**
```python
# Clear model cache
manager.clear_cache()

# Use smaller models
ner_service = NERService(model_name="ner")  # Instead of "ner_large"
```

**3. Slow performance:**
```bash
# Enable GPU if available
ENABLE_GPU=true

# Use smaller, faster models
# Use batching for multiple texts
```

**4. Import errors:**
```bash
# Install missing dependencies
pip install torch transformers sentence-transformers
```

---

## 🎓 Examples

### Example 1: News Article Analysis

```python
article = """
Taliban forces entered Kabul yesterday. The UN expressed concern 
about the humanitarian situation. Fighting continues in Kandahar.
"""

# Extract entities
entities = ner_service.extract_entities(article)
locations = [e for e in entities if e["entity_type"] == "LOCATION"]
# → ["Kabul", "Kandahar"]

# Sentiment
sentiment = sentiment_service.analyze(article)
# → {"sentiment": "negative", "score": 0.82}

# Topics
topics = classifier.classify_isr_topic(article)
# → [{"category": "security threat", "score": 0.88}, ...]

# Threats
threats = threat_service.detect_threats(article)
# → {"threat_detected": True, "threat_score": 0.72, "threat_level": "high"}
```

### Example 2: Duplicate Detection

```python
articles = [
    "Taliban capture Kandahar",
    "Taliban forces take control of Kandahar",
    "UN discusses aid distribution",
    ...
]

duplicates = embeddings_service.find_duplicates(articles, threshold=0.85)
# → [(0, 1, 0.92), ...]  # Articles 0 and 1 are 92% similar
```

### Example 3: Semantic Search

```python
query = "Security threats near Pakistan border"

results = embeddings_service.semantic_search(
    query=query,
    corpus=all_articles,
    top_k=10
)
# Returns 10 most semantically relevant articles
```

---

## 📚 Additional Resources

- **Transformers Docs:** https://huggingface.co/docs/transformers
- **Sentence Transformers:** https://www.sbert.net/
- **Model Hub:** https://huggingface.co/models

---

## 🎯 Summary

The ISR Platform now includes:

✅ **5 ML Services:**
- Named Entity Recognition
- Sentiment Analysis
- Zero-Shot Classification
- Threat Detection (Ensemble)
- Semantic Embeddings

✅ **20+ REST API Endpoints**
✅ **Automatic Stream Processing Integration**
✅ **GPU Support**
✅ **Model Caching & Management**
✅ **Production-Ready Performance**

**Ready to use out of the box!** 🚀
