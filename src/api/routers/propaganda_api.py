"""API endpoints for propaganda detection and news verification."""

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class PropagandaRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for propaganda")


class NewsVerificationRequest(BaseModel):
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content")
    source: str = Field(None, description="Source URL")


class NarrativeComparisonRequest(BaseModel):
    texts: List[str] = Field(..., description="Multiple texts to compare")
    threshold: float = Field(0.8, description="Similarity threshold")


@router.post("/propaganda/detect")
async def detect_propaganda(request: PropagandaRequest) -> Dict[str, Any]:
    """Detect propaganda techniques in text."""
    from src.services.ml.propaganda_detector import get_propaganda_detector
    
    detector = get_propaganda_detector()
    result = detector.detect_propaganda(request.text)
    return result


@router.post("/propaganda/compare-narratives")
async def compare_narratives(request: NarrativeComparisonRequest) -> Dict[str, Any]:
    """Compare multiple texts for coordinated propaganda."""
    from src.services.ml.propaganda_detector import get_propaganda_detector
    
    detector = get_propaganda_detector()
    result = detector.compare_narratives(request.texts, request.threshold)
    return result


@router.post("/news/verify")
async def verify_news(request: NewsVerificationRequest) -> Dict[str, Any]:
    """Verify news article credibility."""
    from src.services.ml.news_verifier import get_news_verifier
    
    verifier = get_news_verifier()
    result = verifier.verify_news(
        title=request.title,
        content=request.content,
        source=request.source,
    )
    return result


@router.get("/propaganda/techniques")
async def get_propaganda_techniques() -> Dict[str, Any]:
    """Get list of detectable propaganda techniques."""
    return {
        "techniques": [
            {"id": 1, "name": "Loaded Language", "description": "Using emotional/biased words"},
            {"id": 2, "name": "Name Calling", "description": "Labeling opponents negatively"},
            {"id": 3, "name": "Repetition", "description": "Repeating messages"},
            {"id": 4, "name": "Exaggeration", "description": "Overstating facts"},
            {"id": 5, "name": "Appeal to Fear", "description": "Exploiting fears"},
            {"id": 6, "name": "Doubt", "description": "Questioning credibility"},
            {"id": 7, "name": "Flag-Waving", "description": "Patriotism appeals"},
            {"id": 8, "name": "Oversimplification", "description": "Simple cause-effect"},
            {"id": 9, "name": "Slogans", "description": "Catchy phrases"},
            {"id": 10, "name": "Appeal to Authority", "description": "Expert claims"},
            {"id": 11, "name": "Black-and-White", "description": "Only two options"},
            {"id": 12, "name": "Thought-terminating Cliché", "description": "Stopping discussion"},
            {"id": 13, "name": "Whataboutism", "description": "Deflecting with 'what about'"},
            {"id": 14, "name": "Bandwagon", "description": "Everyone's doing it"},
        ]
    }
