"""Comprehensive ML system testing script.

Tests all ML services with real-world examples.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class Colors:
    """Terminal colors."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}→ {text}{Colors.RESET}")


def print_result(label: str, value: any):
    """Print result."""
    print(f"{Colors.YELLOW}{label}:{Colors.RESET} {value}")


async def test_ner_service():
    """Test Named Entity Recognition."""
    print_header("Testing Named Entity Recognition (NER)")
    
    try:
        from src.services.ml import get_ner_service
        
        ner = get_ner_service()
        
        test_texts = [
            "Taliban forces entered Kabul yesterday under UN supervision.",
            "President Biden discussed Afghanistan with NATO allies in Brussels.",
            "The Red Cross is providing aid in Kandahar and Helmand provinces.",
        ]
        
        for i, text in enumerate(test_texts, 1):
            print_info(f"Test {i}: {text[:60]}...")
            
            start = time.time()
            entities = ner.extract_entities(text, min_confidence=0.6)
            elapsed = time.time() - start
            
            print_result("  Entities found", len(entities))
            print_result("  Time", f"{elapsed*1000:.1f}ms")
            
            # Show entities by type
            for entity in entities[:5]:  # Show first 5
                print(f"    - {entity['entity_type']:15s} {entity['text']:20s} ({entity['confidence']:.2f})")
            
            # Test specific extractors
            locations = ner.extract_locations(text)
            orgs = ner.extract_organizations(text)
            persons = ner.extract_persons(text)
            
            print_result("  Locations", locations)
            print_result("  Organizations", orgs)
            print_result("  Persons", persons)
            print()
        
        print_success("NER Service: PASSED")
        return True
        
    except Exception as e:
        print_error(f"NER Service: FAILED - {e}")
        return False


async def test_sentiment_service():
    """Test Sentiment Analysis."""
    print_header("Testing Sentiment Analysis")
    
    try:
        from src.services.ml import get_sentiment_service
        
        sentiment = get_sentiment_service()
        
        test_cases = [
            ("Peace agreement brings hope for Afghanistan's future.", "positive"),
            ("Deadly explosion kills dozens in Kabul market.", "negative"),
            ("Aid distribution scheduled for next week.", "neutral"),
            ("Taliban threaten violence if demands not met.", "negative"),
            ("UN praises successful humanitarian operation.", "positive"),
        ]
        
        correct = 0
        for text, expected in test_cases:
            print_info(f"Text: {text[:60]}...")
            
            start = time.time()
            result = sentiment.analyze(text)
            elapsed = time.time() - start
            
            print_result("  Sentiment", result['sentiment'])
            print_result("  Score", f"{result['score']:.3f}")
            print_result("  Time", f"{elapsed*1000:.1f}ms")
            
            if result['sentiment'] == expected:
                print(f"  {Colors.GREEN}✓ Correct{Colors.RESET}")
                correct += 1
            else:
                print(f"  {Colors.YELLOW}⚠ Expected {expected}{Colors.RESET}")
            print()
        
        accuracy = (correct / len(test_cases)) * 100
        print_result("Accuracy", f"{accuracy:.1f}%")
        
        # Test batch processing
        print_info("Testing batch processing...")
        texts = [tc[0] for tc in test_cases]
        start = time.time()
        batch_results = sentiment.analyze_batch(texts)
        elapsed = time.time() - start
        print_result("  Batch time", f"{elapsed*1000:.1f}ms")
        print_result("  Per-text time", f"{(elapsed/len(texts))*1000:.1f}ms")
        
        # Test statistics
        stats = sentiment.get_sentiment_statistics(texts)
        print_result("  Positive", f"{stats['positive_pct']:.1f}%")
        print_result("  Negative", f"{stats['negative_pct']:.1f}%")
        print_result("  Neutral", f"{stats['neutral_pct']:.1f}%")
        
        print_success("Sentiment Service: PASSED")
        return True
        
    except Exception as e:
        print_error(f"Sentiment Service: FAILED - {e}")
        return False


async def test_classification_service():
    """Test Classification."""
    print_header("Testing Zero-Shot Classification")
    
    try:
        from src.services.ml import get_classification_service
        
        classifier = get_classification_service()
        
        # Test ISR topic classification
        test_texts = [
            "IED discovered near military checkpoint.",
            "Humanitarian aid reaches displaced families.",
            "Border security forces increase patrols.",
            "Economic sanctions impact local markets.",
        ]
        
        for text in test_texts:
            print_info(f"Text: {text}")
            
            start = time.time()
            topics = classifier.classify_isr_topic(text, top_k=3)
            elapsed = time.time() - start
            
            print_result("  Time", f"{elapsed*1000:.1f}ms")
            print("  Topics:")
            for topic in topics:
                print(f"    - {topic['category']:25s} ({topic['score']:.3f})")
            print()
        
        # Test threat level
        print_info("Testing threat level classification...")
        threat_texts = [
            "Routine patrol completed without incident.",
            "Suspicious activity reported near embassy.",
            "Active shooter situation in progress.",
        ]
        
        for text in threat_texts:
            print_info(f"  {text[:50]}...")
            result = classifier.classify_threat_level(text)
            print_result("    Threat Level", result['threat_level'])
            print_result("    Confidence", f"{result['confidence']:.3f}")
        
        # Test Afghanistan relevance
        print_info("\nTesting Afghanistan relevance...")
        test_relevance = [
            ("Taliban activity in Kandahar province", True),
            ("Election results in United States", False),
            ("Kabul airport security measures", True),
        ]
        
        for text, expected in test_relevance:
            result = classifier.is_relevant_to_afghanistan(text)
            status = "✓" if result['is_relevant'] == expected else "✗"
            print(f"  {status} {text[:50]}... → {result['is_relevant']} ({result['confidence']:.2f})")
        
        print_success("Classification Service: PASSED")
        return True
        
    except Exception as e:
        print_error(f"Classification Service: FAILED - {e}")
        return False


async def test_threat_detection():
    """Test Threat Detection."""
    print_header("Testing Threat Detection (Ensemble)")
    
    try:
        from src.services.ml import get_threat_detection_service
        
        threat = get_threat_detection_service()
        
        test_cases = [
            ("IED attack kills soldiers near Kabul.", "high"),
            ("Taliban threaten violence against civilians.", "high"),
            ("Routine patrol scheduled for tomorrow.", "low"),
            ("Humanitarian aid distribution proceeds smoothly.", "low"),
            ("Bomb threat at embassy compound.", "critical"),
        ]
        
        for text, expected_level in test_cases:
            print_info(f"Text: {text}")
            
            start = time.time()
            result = threat.detect_threats(text, include_details=True)
            elapsed = time.time() - start
            
            print_result("  Threat Detected", result['threat_detected'])
            print_result("  Threat Score", f"{result['threat_score']:.3f}")
            print_result("  Threat Level", result['threat_level'])
            print_result("  Time", f"{elapsed*1000:.1f}ms")
            
            if 'details' in result:
                details = result['details']
                print("  Details:")
                print(f"    Keyword Score: {details['keyword_score']:.3f}")
                print(f"    Sentiment Score: {details['sentiment_score']:.3f}")
                print(f"    Classification Score: {details['classification_score']:.3f}")
                print(f"    Entity Score: {details['entity_score']:.3f}")
                
                if details.get('keyword_matches'):
                    print("    Keywords:", list(details['keyword_matches'].keys())[:3])
            
            print()
        
        # Test batch processing
        print_info("Testing batch threat detection...")
        texts = [tc[0] for tc in test_cases]
        start = time.time()
        batch_results = threat.batch_detect(texts)
        elapsed = time.time() - start
        print_result("  Batch time", f"{elapsed*1000:.1f}ms")
        print_result("  Threats detected", sum(1 for r in batch_results if r['threat_detected']))
        
        # Test summary
        summary = threat.get_threat_summary(texts)
        print_result("  Threat rate", f"{summary['threat_rate']:.1f}%")
        print_result("  By level", summary['by_level'])
        
        print_success("Threat Detection: PASSED")
        return True
        
    except Exception as e:
        print_error(f"Threat Detection: FAILED - {e}")
        return False


async def test_embedding_service():
    """Test Embeddings and Similarity."""
    print_header("Testing Semantic Embeddings & Similarity")
    
    try:
        from src.services.ml import get_embedding_service
        
        embeddings = get_embedding_service()
        
        # Test similarity
        print_info("Testing similarity computation...")
        similar_pairs = [
            ("Military forces deploy to region", "Armed troops sent to area"),
            ("Taliban capture city", "Militants take control of urban center"),
        ]
        
        different_pairs = [
            ("Military operation", "Economic development"),
            ("Security threat", "Humanitarian aid"),
        ]
        
        print("Similar texts:")
        for text1, text2 in similar_pairs:
            sim = embeddings.similarity(text1, text2)
            print(f"  {sim:.3f} - {text1[:30]}... ↔ {text2[:30]}...")
        
        print("\nDifferent texts:")
        for text1, text2 in different_pairs:
            sim = embeddings.similarity(text1, text2)
            print(f"  {sim:.3f} - {text1[:30]}... ↔ {text2[:30]}...")
        
        # Test semantic search
        print_info("\nTesting semantic search...")
        query = "Taliban military operations"
        corpus = [
            "Taliban forces conduct operations in Helmand",
            "UN distributes food aid to refugees",
            "Militant activity reported near border",
            "Economic sanctions impact trade",
            "Insurgent groups increase attacks",
        ]
        
        results = embeddings.semantic_search(query, corpus, top_k=3)
        print_result("  Query", query)
        print("  Top results:")
        for i, result in enumerate(results, 1):
            print(f"    {i}. [{result['score']:.3f}] {result['text'][:50]}...")
        
        # Test duplicate detection
        print_info("\nTesting duplicate detection...")
        texts_with_dupes = [
            "Taliban capture Kandahar",
            "Taliban take control of Kandahar",
            "UN meeting scheduled",
            "Taliban forces seize Kandahar city",
            "Economic aid package announced",
        ]
        
        duplicates = embeddings.find_duplicates(texts_with_dupes, threshold=0.75)
        print_result("  Duplicates found", len(duplicates))
        for idx1, idx2, sim in duplicates:
            print(f"    [{sim:.3f}] {texts_with_dupes[idx1][:40]}...")
            print(f"            {texts_with_dupes[idx2][:40]}...")
        
        # Test clustering
        print_info("\nTesting document clustering...")
        cluster_texts = [
            "Military operation in progress",
            "Humanitarian aid distribution",
            "Armed forces engage militants",
            "Food supplies reach refugees",
            "Security forces patrol border",
            "Medical aid provided",
        ]
        
        clusters = embeddings.cluster_texts(cluster_texts, n_clusters=2)
        print("  Clusters:")
        for i in range(2):
            docs = [cluster_texts[j] for j, c in enumerate(clusters) if c == i]
            print(f"    Cluster {i}: {len(docs)} docs")
            for doc in docs:
                print(f"      - {doc}")
        
        print_success("Embedding Service: PASSED")
        return True
        
    except Exception as e:
        print_error(f"Embedding Service: FAILED - {e}")
        return False


async def test_model_manager():
    """Test Model Manager."""
    print_header("Testing Model Manager")
    
    try:
        from src.services.ml import get_model_manager
        
        manager = get_model_manager()
        
        # Get memory usage
        memory = manager.get_memory_usage()
        print_result("Device", memory['device'])
        print_result("Models loaded", memory['models_loaded'])
        print_result("Tokenizers loaded", memory['tokenizers_loaded'])
        print_result("Pipelines loaded", memory['pipelines_loaded'])
        
        if 'gpu_memory_allocated' in memory:
            print_result("GPU Memory", f"{memory['gpu_memory_allocated']:.2f} GB")
        
        # Show model registry
        print_info("\nModel Registry:")
        for name, model_id in list(manager.models.items())[:5]:
            print(f"  {name:20s} → {model_id}")
        
        print_success("Model Manager: PASSED")
        return True
        
    except Exception as e:
        print_error(f"Model Manager: FAILED - {e}")
        return False


async def run_performance_benchmarks():
    """Run performance benchmarks."""
    print_header("Performance Benchmarks")
    
    try:
        from src.services.ml import (
            get_ner_service,
            get_sentiment_service,
            get_classification_service,
            get_threat_detection_service,
            get_embedding_service,
        )
        
        test_text = "Taliban forces entered Kabul yesterday amid international concern."
        test_texts = [test_text] * 10
        
        benchmarks = []
        
        # NER
        ner = get_ner_service()
        start = time.time()
        for _ in range(10):
            ner.extract_entities(test_text)
        elapsed = time.time() - start
        benchmarks.append(("NER (single)", elapsed / 10 * 1000))
        
        # Sentiment
        sentiment = get_sentiment_service()
        start = time.time()
        sentiment.analyze_batch(test_texts)
        elapsed = time.time() - start
        benchmarks.append(("Sentiment (batch 10)", elapsed / 10 * 1000))
        
        # Classification
        classifier = get_classification_service()
        start = time.time()
        for _ in range(5):
            classifier.classify_isr_topic(test_text)
        elapsed = time.time() - start
        benchmarks.append(("Classification (single)", elapsed / 5 * 1000))
        
        # Threat Detection
        threat = get_threat_detection_service()
        start = time.time()
        for _ in range(10):
            threat.detect_threats(test_text, include_details=False)
        elapsed = time.time() - start
        benchmarks.append(("Threat Detection (single)", elapsed / 10 * 1000))
        
        # Embeddings
        embeddings_svc = get_embedding_service()
        start = time.time()
        embeddings_svc.encode(test_texts)
        elapsed = time.time() - start
        benchmarks.append(("Embeddings (batch 10)", elapsed / 10 * 1000))
        
        print("\nPerformance (avg time per operation):")
        print(f"{'Operation':<30s} {'Time (ms)':>12s}")
        print("-" * 44)
        for op, ms in benchmarks:
            print(f"{op:<30s} {ms:>11.1f}ms")
        
        print_success("Benchmarks: COMPLETED")
        return True
        
    except Exception as e:
        print_error(f"Benchmarks: FAILED - {e}")
        return False


async def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("=" * 70)
    print("  ISR PLATFORM - ML SYSTEM COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"{Colors.RESET}\n")
    
    results = []
    
    # Run all tests
    results.append(("NER Service", await test_ner_service()))
    results.append(("Sentiment Service", await test_sentiment_service()))
    results.append(("Classification Service", await test_classification_service()))
    results.append(("Threat Detection", await test_threat_detection()))
    results.append(("Embedding Service", await test_embedding_service()))
    results.append(("Model Manager", await test_model_manager()))
    results.append(("Performance Benchmarks", await run_performance_benchmarks()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if result else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"  {name:<30s} {status}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
