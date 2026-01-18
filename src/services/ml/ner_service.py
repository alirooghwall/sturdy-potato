"""Named Entity Recognition (NER) service using transformers.

Extracts entities like persons, organizations, locations from text.
"""

import logging
from typing import Any, Dict, List, Optional

from .model_manager import get_model_manager

logger = logging.getLogger(__name__)


class NERService:
    """Named Entity Recognition service.
    
    Uses transformer models to extract entities from text:
    - PERSON: People, including fictional
    - ORGANIZATION: Companies, agencies, institutions
    - LOCATION: Countries, cities, states, geographical regions
    - MISC: Miscellaneous entities
    
    Advanced models also support:
    - GPE: Geopolitical entities
    - DATE: Dates
    - EVENT: Named events
    - FACILITY: Buildings, airports, highways
    - PRODUCT: Vehicles, weapons, foods
    """

    def __init__(self, model_name: str = "ner"):
        """Initialize NER service.
        
        Args:
            model_name: Model to use (ner, ner_large, multilingual_ner)
        """
        self.model_name = model_name
        self.model_manager = get_model_manager()
        self._pipeline = None
        
        logger.info(f"NER service initialized with model: {model_name}")
    
    def _get_pipeline(self):
        """Lazy load the NER pipeline."""
        if self._pipeline is None:
            logger.info("Loading NER pipeline...")
            self._pipeline = self.model_manager.create_pipeline(
                "ner",
                self.model_name,
                aggregation_strategy="simple",  # Merge sub-word tokens
            )
            logger.info("✓ NER pipeline loaded")
        return self._pipeline
    
    def extract_entities(
        self,
        text: str,
        min_confidence: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Extract named entities from text.
        
        Args:
            text: Input text
            min_confidence: Minimum confidence threshold (0-1)
        
        Returns:
            List of entities with type, text, and confidence
        """
        if not text or not text.strip():
            return []
        
        try:
            pipeline = self._get_pipeline()
            
            # Run inference
            results = pipeline(text)
            
            # Filter by confidence and format
            entities = []
            for entity in results:
                if entity["score"] >= min_confidence:
                    entities.append({
                        "entity_type": entity["entity_group"],
                        "text": entity["word"].strip(),
                        "confidence": float(entity["score"]),
                        "start": entity["start"],
                        "end": entity["end"],
                    })
            
            logger.debug(f"Extracted {len(entities)} entities from text")
            return entities
        
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def extract_entities_by_type(
        self,
        text: str,
        entity_type: str,
        min_confidence: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Extract specific type of entities.
        
        Args:
            text: Input text
            entity_type: Entity type to extract (PERSON, ORGANIZATION, LOCATION, etc.)
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of entities of specified type
        """
        all_entities = self.extract_entities(text, min_confidence)
        return [
            e for e in all_entities
            if e["entity_type"].upper() == entity_type.upper()
        ]
    
    def get_unique_entities(
        self,
        text: str,
        min_confidence: float = 0.5,
    ) -> Dict[str, List[str]]:
        """Get unique entities grouped by type.
        
        Args:
            text: Input text
            min_confidence: Minimum confidence threshold
        
        Returns:
            Dictionary mapping entity types to lists of unique entity texts
        """
        entities = self.extract_entities(text, min_confidence)
        
        grouped = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            entity_text = entity["text"]
            
            if entity_type not in grouped:
                grouped[entity_type] = set()
            
            grouped[entity_type].add(entity_text)
        
        # Convert sets to sorted lists
        return {
            entity_type: sorted(list(entities))
            for entity_type, entities in grouped.items()
        }
    
    def extract_locations(self, text: str, min_confidence: float = 0.5) -> List[str]:
        """Extract location entities.
        
        Args:
            text: Input text
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of unique location names
        """
        locations = self.extract_entities_by_type(text, "LOCATION", min_confidence)
        # Also check for GPE (Geopolitical Entity) if available
        gpe = self.extract_entities_by_type(text, "GPE", min_confidence)
        
        all_locations = locations + gpe
        unique_locations = list(set([loc["text"] for loc in all_locations]))
        return sorted(unique_locations)
    
    def extract_organizations(self, text: str, min_confidence: float = 0.5) -> List[str]:
        """Extract organization entities.
        
        Args:
            text: Input text
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of unique organization names
        """
        orgs = self.extract_entities_by_type(text, "ORGANIZATION", min_confidence)
        # Some models use ORG
        org_short = self.extract_entities_by_type(text, "ORG", min_confidence)
        
        all_orgs = orgs + org_short
        unique_orgs = list(set([org["text"] for org in all_orgs]))
        return sorted(unique_orgs)
    
    def extract_persons(self, text: str, min_confidence: float = 0.5) -> List[str]:
        """Extract person entities.
        
        Args:
            text: Input text
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of unique person names
        """
        persons = self.extract_entities_by_type(text, "PERSON", min_confidence)
        # Some models use PER
        per_short = self.extract_entities_by_type(text, "PER", min_confidence)
        
        all_persons = persons + per_short
        unique_persons = list(set([person["text"] for person in all_persons]))
        return sorted(unique_persons)


# Global instance
_ner_service: Optional[NERService] = None


def get_ner_service() -> NERService:
    """Get the global NER service instance."""
    global _ner_service
    if _ner_service is None:
        _ner_service = NERService()
    return _ner_service
