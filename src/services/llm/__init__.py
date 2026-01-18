"""LLM integration services for ISR Platform.

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Local models (Ollama, LLaMA)
- Azure OpenAI
"""

from .llm_service import LLMService, get_llm_service
from .report_generator import ReportGenerator, get_report_generator
from .conversational_query import ConversationalQuery, get_conversational_query
from .insight_discovery import InsightDiscovery, get_insight_discovery
from .anomaly_explainer import AnomalyExplainer, get_anomaly_explainer

__all__ = [
    "LLMService",
    "get_llm_service",
    "ReportGenerator",
    "get_report_generator",
    "ConversationalQuery",
    "get_conversational_query",
    "InsightDiscovery",
    "get_insight_discovery",
    "AnomalyExplainer",
    "get_anomaly_explainer",
]
