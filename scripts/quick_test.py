"""Quick test to verify basic ML setup without loading models."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all ML modules can be imported."""
    print("Testing imports...")
    
    try:
        print("  ✓ Importing torch...", end=" ")
        import torch
        print(f"OK (version {torch.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Importing transformers...", end=" ")
        import transformers
        print(f"OK (version {transformers.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Importing sentence_transformers...", end=" ")
        import sentence_transformers
        print(f"OK (version {sentence_transformers.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    try:
        print("  ✓ Importing sklearn...", end=" ")
        import sklearn
        print(f"OK (version {sklearn.__version__})")
    except ImportError as e:
        print(f"FAILED: {e}")
        return False
    
    return True


def test_ml_services():
    """Test that ML services can be imported."""
    print("\nTesting ML service imports...")
    
    services = [
        "get_model_manager",
        "get_ner_service",
        "get_sentiment_service",
        "get_classification_service",
        "get_threat_detection_service",
        "get_embedding_service",
        "get_summarization_service",
        "get_translation_service",
        "get_monitoring_service",
    ]
    
    try:
        from src.services import ml
        
        for service in services:
            if hasattr(ml, service):
                print(f"  ✓ {service}")
            else:
                print(f"  ✗ {service} - NOT FOUND")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to import ML services: {e}")
        return False


def test_device():
    """Test device availability (CPU/GPU)."""
    print("\nTesting device...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"  ✓ GPU available: {torch.cuda.get_device_name(0)}")
            print(f"    GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            print("  ✓ Using CPU (no GPU detected)")
        
        return True
    except Exception as e:
        print(f"  ✗ Device test failed: {e}")
        return False


def test_model_manager():
    """Test model manager initialization."""
    print("\nTesting Model Manager...")
    
    try:
        from src.services.ml import get_model_manager
        
        manager = get_model_manager()
        print(f"  ✓ Model Manager initialized")
        print(f"    Device: {manager.device}")
        print(f"    Cache dir: {manager.cache_dir}")
        print(f"    GPU enabled: {manager.use_gpu}")
        print(f"    Models in registry: {len(manager.models)}")
        
        return True
    except Exception as e:
        print(f"  ✗ Model Manager test failed: {e}")
        return False


def test_monitoring():
    """Test monitoring service."""
    print("\nTesting Monitoring Service...")
    
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        print(f"  ✓ Monitoring Service initialized")
        
        # Get metrics
        metrics = monitoring.get_system_metrics()
        print(f"    Uptime: {metrics['uptime_seconds']:.1f}s")
        print(f"    Total requests: {metrics['total_requests']}")
        
        return True
    except Exception as e:
        print(f"  ✗ Monitoring test failed: {e}")
        return False


def main():
    """Run quick tests."""
    print("=" * 70)
    print("  ISR PLATFORM - ML QUICK TEST")
    print("=" * 70)
    print()
    
    results = []
    
    # Run tests
    results.append(("Package Imports", test_imports()))
    results.append(("ML Services", test_ml_services()))
    results.append(("Device Detection", test_device()))
    results.append(("Model Manager", test_model_manager()))
    results.append(("Monitoring Service", test_monitoring()))
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name:<30s} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        print("\nYou can now run full tests with:")
        print("  python scripts/test_ml_system.py")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        print("\nPlease ensure all dependencies are installed:")
        print("  pip install torch transformers sentence-transformers scikit-learn")
        return 1


if __name__ == "__main__":
    sys.exit(main())
