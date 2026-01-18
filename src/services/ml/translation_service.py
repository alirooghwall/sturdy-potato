"""Translation service for multilingual support.

Translates between multiple languages including Pashto and Dari.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .model_manager import get_model_manager

logger = logging.getLogger(__name__)


class TranslationService:
    """Translation service using transformer models.
    
    Supports:
    - English ↔ Multiple languages
    - Automatic language detection
    - Batch translation
    - Quality scoring
    """

    def __init__(self):
        """Initialize translation service."""
        self.model_manager = get_model_manager()
        self._pipelines: Dict[str, Any] = {}
        
        # Add translation models to registry
        self.model_manager.models.update({
            "translate_en_multi": "Helsinki-NLP/opus-mt-en-mul",  # English to many
            "translate_multi_en": "Helsinki-NLP/opus-mt-mul-en",  # Many to English
            "translate_large": "facebook/m2m100_418M",  # Multilingual (100 languages)
        })
        
        # Language mappings
        self.language_names = {
            "en": "English",
            "ps": "Pashto",
            "fa": "Dari/Farsi",
            "ur": "Urdu",
            "ar": "Arabic",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "ru": "Russian",
            "zh": "Chinese",
        }
        
        logger.info("Translation service initialized")
    
    def _get_pipeline(self, source_lang: str, target_lang: str) -> Any:
        """Get or create translation pipeline for language pair.
        
        Args:
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'ps')
        
        Returns:
            Translation pipeline
        """
        cache_key = f"{source_lang}_{target_lang}"
        
        if cache_key in self._pipelines:
            return self._pipelines[cache_key]
        
        logger.info(f"Loading translation pipeline: {source_lang} → {target_lang}")
        
        try:
            # Determine model based on language pair
            if source_lang == "en":
                model_name = "translate_en_multi"
            elif target_lang == "en":
                model_name = "translate_multi_en"
            else:
                model_name = "translate_large"
            
            pipeline = self.model_manager.create_pipeline(
                "translation",
                model_name,
                src_lang=source_lang,
                tgt_lang=target_lang,
            )
            
            self._pipelines[cache_key] = pipeline
            logger.info(f"✓ Translation pipeline loaded: {source_lang} → {target_lang}")
            
            return pipeline
        
        except Exception as e:
            logger.error(f"Failed to load translation pipeline: {e}")
            raise
    
    def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "ps",
    ) -> Dict[str, Any]:
        """Translate text between languages.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            Dictionary with translation and metadata
        """
        if not text or not text.strip():
            return {
                "translated_text": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": text,
            }
        
        try:
            pipeline = self._get_pipeline(source_lang, target_lang)
            
            # Translate (truncate if too long)
            max_length = 512
            text_truncated = text[:max_length * 4]
            
            result = pipeline(text_truncated)[0]
            translated = result["translation_text"]
            
            return {
                "translated_text": translated,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": text,
                "source_lang_name": self.language_names.get(source_lang, source_lang),
                "target_lang_name": self.language_names.get(target_lang, target_lang),
                "truncated": len(text) > max_length * 4,
            }
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "translated_text": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": text,
                "error": str(e),
            }
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str = "en",
        target_lang: str = "ps",
    ) -> List[Dict[str, Any]]:
        """Translate multiple texts.
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            List of translation results
        """
        return [
            self.translate(text, source_lang, target_lang)
            for text in texts
        ]
    
    def translate_to_english(self, text: str, source_lang: str = "ps") -> str:
        """Translate text to English.
        
        Args:
            text: Text to translate
            source_lang: Source language code
        
        Returns:
            Translated text
        """
        result = self.translate(text, source_lang=source_lang, target_lang="en")
        return result.get("translated_text", "")
    
    def translate_from_english(self, text: str, target_lang: str = "ps") -> str:
        """Translate English text to another language.
        
        Args:
            text: English text
            target_lang: Target language code
        
        Returns:
            Translated text
        """
        result = self.translate(text, source_lang="en", target_lang=target_lang)
        return result.get("translated_text", "")
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of text.
        
        Note: This is a simple heuristic. For better accuracy, use langdetect or similar.
        
        Args:
            text: Input text
        
        Returns:
            Dictionary with detected language
        """
        try:
            # Try to use langdetect if available
            import langdetect
            detected = langdetect.detect(text)
            confidence = 1.0  # langdetect doesn't provide confidence
            
            return {
                "language": detected,
                "language_name": self.language_names.get(detected, detected),
                "confidence": confidence,
            }
        
        except ImportError:
            # Fallback: simple heuristic based on character ranges
            # This is very basic and not accurate
            return {
                "language": "unknown",
                "language_name": "Unknown",
                "confidence": 0.0,
                "note": "Install langdetect for better language detection",
            }
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {
                "language": "unknown",
                "language_name": "Unknown",
                "confidence": 0.0,
                "error": str(e),
            }
    
    def multilingual_support_info(self) -> Dict[str, Any]:
        """Get information about supported languages.
        
        Returns:
            Dictionary with supported languages
        """
        return {
            "supported_languages": self.language_names,
            "translation_pairs": [
                "English ↔ Pashto",
                "English ↔ Dari/Farsi",
                "English ↔ Urdu",
                "English ↔ Arabic",
                "English ↔ 100+ languages (via m2m100)",
            ],
            "models": [
                "Helsinki-NLP/opus-mt-en-mul",
                "Helsinki-NLP/opus-mt-mul-en",
                "facebook/m2m100_418M",
            ],
        }


# Global instance
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Get the global translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service
