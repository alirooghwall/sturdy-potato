# ML System Testing Guide

## Quick Start

The ML system is ready to test! Here's how to verify everything works.

---

## ✅ Prerequisites Check

Before testing, ensure you have:

```bash
# Check Python version (3.8+ required)
python --version

# Check if dependencies are installed
pip list | grep torch
pip list | grep transformers
pip list | grep sentence-transformers
```

---

## 🚀 Installation

If dependencies are missing, install them:

```bash
# Install ML dependencies (CPU version)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers accelerate scikit-learn

# For GPU support (if you have CUDA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 🧪 Testing Options

### Option 1: Quick Import Test (No Model Download)

Create and run a simple test:

```python
# test_imports.py
import sys

print("Testing ML imports...")

try:
    import torch
    print(f"✓ PyTorch: {torch.__version__}")
except ImportError as e:
    print(f"✗ PyTorch: {e}")
    sys.exit(1)

try:
    import transformers
    print(f"✓ Transformers: {transformers.__version__}")
except ImportError as e:
    print(f"✗ Transformers: {e}")
    sys.exit(1)

try:
    import sentence_transformers
    print(f"✓ Sentence Transformers: {sentence_transformers.__version__}")
except ImportError as e:
    print(f"✗ Sentence Transformers: {e}")
    sys.exit(1)

try:
    import sklearn
    print(f"✓ Scikit-learn: {sklearn.__version__}")
except ImportError as e:
    print(f"✗ Scikit-learn: {e}")
    sys.exit(1)

# Test ML service imports
sys.path.insert(0, ".")
try:
    from src.services.ml import (
        get_model_manager,
        get_ner_service,
        get_sentiment_service,
        get_monitoring_service,
    )
    print("✓ ML Services import successfully")
except Exception as e:
    print(f"✗ ML Services: {e}")
    sys.exit(1)

print("\n✓ All imports successful!")
print("\nYou can now:")
print("  1. Run full tests: python scripts/test_ml_system.py")
print("  2. Start API: docker-compose up -d")
print("  3. Test API: curl http://localhost:8000/api/v1/ml-api/models/status")
```

Run it:
```bash
python test_imports.py
```

---

### Option 2: API Testing (Recommended)

Start the API server and test via REST:

```bash
# Start the server
docker-compose up -d

# Check API is running
curl http://localhost:8000/health

# Test ML API status (no model loading)
curl http://localhost:8000/api/v1/ml-api/models/status

# Get monitoring metrics
curl http://localhost:8000/api/v1/ml-api/monitoring/system
```

---

### Option 3: Comprehensive Test Suite

Run the full test suite (downloads models on first run):

```bash
python scripts/test_ml_system.py
```

**Note:** First run will download transformer models (~1-2 GB) which takes 5-30 minutes.

---

## 📊 Testing Individual Services

### Test NER (Named Entity Recognition)

```bash
curl -X POST http://localhost:8000/api/v1/ml-api/ner/extract \
  -H "Content-Type: application/json" \
  -d '{"text":"Taliban forces entered Kabul yesterday","min_confidence":0.5}'
```

### Test Sentiment Analysis

```bash
curl -X POST http://localhost:8000/api/v1/ml-api/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Peace agreement brings hope for the future"}'
```

### Test Threat Detection

```bash
curl -X POST http://localhost:8000/api/v1/ml-api/threat/detect \
  -H "Content-Type: application/json" \
  -d '{"text":"IED attack reported in Kandahar","include_details":true}'
```

### Test Summarization

```bash
curl -X POST http://localhost:8000/api/v1/ml-api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"Long article text here...","max_length":100}'
```

### Test Translation

```bash
curl -X POST http://localhost:8000/api/v1/ml-api/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","source_lang":"en","target_lang":"ps"}'
```

### Test Similarity

```bash
curl -X POST http://localhost:8000/api/v1/ml-api/similarity \
  -H "Content-Type: application/json" \
  -d '{"text1":"Military operation","text2":"Armed forces deployment"}'
```

---

## 🐛 Troubleshooting

### Issue: ImportError for torch/transformers

**Solution:**
```bash
pip install torch transformers sentence-transformers scikit-learn accelerate
```

### Issue: CUDA errors

**Solution:** Use CPU version:
```bash
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue: Models downloading slowly

**Solution:** 
- Be patient (first download takes time)
- Check internet connection
- Models are cached in `./models` directory for future use

### Issue: Out of memory

**Solution:**
- Use smaller models (edit `model_manager.py`)
- Enable swap/virtual memory
- Close other applications
- Consider using GPU with more memory

### Issue: API not responding

**Solution:**
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs api

# Restart services
docker-compose restart
```

---

## 📈 Performance Monitoring

Monitor ML performance in real-time:

```bash
# System metrics
curl http://localhost:8000/api/v1/ml-api/monitoring/system

# Model usage
curl http://localhost:8000/api/v1/ml-api/monitoring/models

# Request rate
curl http://localhost:8000/api/v1/ml-api/monitoring/request-rate

# Top models
curl http://localhost:8000/api/v1/ml-api/monitoring/top-models

# Slow requests
curl http://localhost:8000/api/v1/ml-api/monitoring/slow-requests
```

---

## ✅ Expected Results

### Successful Test Output

```
Testing ML imports...
✓ PyTorch: 2.1.0
✓ Transformers: 4.35.0
✓ Sentence Transformers: 2.2.2
✓ Scikit-learn: 1.3.0
✓ ML Services import successfully

✓ All imports successful!
```

### API Response Example

```json
{
  "status": "online",
  "device": "cpu",
  "models_loaded": 3,
  "memory": {
    "models_loaded": 3,
    "device": "cpu"
  }
}
```

---

## 🎯 Next Steps After Testing

Once tests pass:

1. **Explore API Documentation**
   - Visit http://localhost:8000/docs
   - Interactive Swagger UI

2. **Read Documentation**
   - `docs/ML_INTEGRATION_GUIDE.md` - Complete ML guide
   - `docs/NEWS_SOURCES_GUIDE.md` - Data ingestion guide
   - `docs/INGESTION_GUIDE.md` - System architecture

3. **Try Examples**
   - Check `tests/test_ml_services.py` for code examples
   - Review `scripts/test_ml_system.py` for usage patterns

4. **Monitor Performance**
   - Use monitoring endpoints
   - Track model usage and latency

5. **Optimize**
   - Enable GPU if available
   - Tune model selection for your use case
   - Adjust batch sizes

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs api`
2. Review documentation in `docs/`
3. Check GitHub issues (if applicable)
4. Verify all dependencies are installed

---

## 📊 Test Checklist

- [ ] Python 3.8+ installed
- [ ] ML dependencies installed (torch, transformers, etc.)
- [ ] Import test passes
- [ ] API server starts successfully
- [ ] API health check returns 200
- [ ] ML model status endpoint works
- [ ] At least one ML service works (NER, sentiment, etc.)
- [ ] Monitoring endpoints return data
- [ ] No errors in docker-compose logs

---

## 🎉 Success Criteria

Your system is ready when:

✅ All imports work without errors
✅ API responds to requests
✅ At least one ML model loads successfully  
✅ Monitoring shows non-zero uptime
✅ No critical errors in logs

**Congratulations! Your ML-powered ISR Platform is operational! 🚀**
