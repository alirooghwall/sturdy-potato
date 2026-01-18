"""Conversational query interface - chat with your intelligence data."""

import logging
from typing import Any, AsyncGenerator
from uuid import UUID, uuid4
from datetime import datetime

from .llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


class ConversationContext:
    """Manage conversation history and context."""
    
    def __init__(self, max_history: int = 10):
        """Initialize conversation context.
        
        Args:
            max_history: Maximum messages to keep in history
        """
        self.conversation_id = uuid4()
        self.messages: list[dict[str, str]] = []
        self.max_history = max_history
        self.metadata: dict[str, Any] = {}
    
    def add_message(self, role: str, content: str):
        """Add message to history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Keep only recent messages
        if len(self.messages) > self.max_history * 2:  # *2 for user+assistant pairs
            self.messages = self.messages[-(self.max_history * 2):]
    
    def get_history(self) -> list[dict[str, str]]:
        """Get conversation history for LLM."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]


class ConversationalQuery:
    """Natural language query interface for intelligence data."""
    
    def __init__(self, llm_service: LLMService | None = None):
        """Initialize conversational query.
        
        Args:
            llm_service: LLM service instance
        """
        self.llm = llm_service or get_llm_service()
        self.conversations: dict[UUID, ConversationContext] = {}
        
        self.system_prompt = """You are an AI intelligence analyst assistant for the ISR Platform. 
You help users query and analyze intelligence data through natural conversation.

You have access to:
- Satellite imagery analysis (deforestation, floods, fires, urban growth, agriculture)
- Narrative tracking and propaganda detection
- Source credibility assessments
- Threat scoring and anomaly detection
- Real-time alerts and events

When users ask questions:
1. Understand their intent
2. Suggest relevant data sources or analyses
3. Provide clear, actionable answers
4. Offer follow-up questions or next steps
5. Use intelligence terminology appropriately

If you need to query data, describe what query would be needed.
Always be helpful, precise, and security-conscious."""
    
    async def query(
        self,
        user_query: str,
        conversation_id: UUID | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process natural language query.
        
        Args:
            user_query: User's question
            conversation_id: Existing conversation ID (creates new if None)
            context_data: Additional context (recent alerts, events, etc.)
        
        Returns:
            Response with answer and suggestions
        """
        # Get or create conversation
        if conversation_id and conversation_id in self.conversations:
            context = self.conversations[conversation_id]
        else:
            context = ConversationContext()
            self.conversations[context.conversation_id] = context
        
        # Add context data if provided
        context_str = ""
        if context_data:
            context_str = f"\n\nCurrent Context:\n{self._format_context(context_data)}"
        
        # Add user message
        context.add_message("user", user_query)
        
        # Build prompt with history
        prompt = user_query + context_str
        
        try:
            # Generate response
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.7,
                max_tokens=1000,
            )
            
            # Add assistant message
            context.add_message("assistant", response)
            
            # Extract suggested queries
            suggestions = self._extract_suggestions(response)
            
            return {
                "conversation_id": str(context.conversation_id),
                "response": response,
                "suggestions": suggestions,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Query error: {e}")
            raise
    
    async def query_stream(
        self,
        user_query: str,
        conversation_id: UUID | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Process query with streaming response.
        
        Args:
            user_query: User's question
            conversation_id: Existing conversation ID
            context_data: Additional context
        
        Yields:
            Response chunks
        """
        # Get or create conversation
        if conversation_id and conversation_id in self.conversations:
            context = self.conversations[conversation_id]
        else:
            context = ConversationContext()
            self.conversations[context.conversation_id] = context
        
        # Add context data
        context_str = ""
        if context_data:
            context_str = f"\n\nCurrent Context:\n{self._format_context(context_data)}"
        
        # Add user message
        context.add_message("user", user_query)
        
        prompt = user_query + context_str
        
        try:
            # Stream response
            full_response = ""
            
            async for chunk in self.llm.generate_stream(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.7,
                max_tokens=1000,
            ):
                full_response += chunk
                yield chunk
            
            # Add complete response to history
            context.add_message("assistant", full_response)
        
        except Exception as e:
            logger.error(f"Streaming query error: {e}")
            raise
    
    async def get_data_insights(
        self,
        data_summary: dict[str, Any],
        insight_type: str = "general",
    ) -> dict[str, Any]:
        """Get AI-generated insights from data.
        
        Args:
            data_summary: Summary of data to analyze
            insight_type: Type of insights (general, trends, anomalies, predictions)
        
        Returns:
            Insights and observations
        """
        system_prompt = """You are an intelligence analyst discovering insights from data.
Identify patterns, anomalies, correlations, and actionable intelligence.
Focus on what's unusual, important, or requires attention."""
        
        prompts = {
            "general": "Analyze this data and provide key insights, patterns, and observations:",
            "trends": "Identify trends, patterns, and directional changes in this data:",
            "anomalies": "Identify anomalies, outliers, and unusual patterns in this data:",
            "predictions": "Based on this data, what predictions or forecasts can you make:",
        }
        
        prompt = f"""{prompts.get(insight_type, prompts['general'])}

{self._format_context(data_summary)}

Provide:
1. Top 3-5 Key Insights
2. Notable Patterns or Trends
3. Items Requiring Attention
4. Recommended Actions"""
        
        try:
            insights = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=1500,
            )
            
            return {
                "insight_id": str(uuid4()),
                "insight_type": insight_type,
                "generated_at": datetime.utcnow().isoformat(),
                "insights": insights,
                "source_data": data_summary,
            }
        
        except Exception as e:
            logger.error(f"Insights error: {e}")
            raise
    
    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context data for prompt."""
        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}: {len(value) if isinstance(value, list) else 'complex data'}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _extract_suggestions(self, response: str) -> list[str]:
        """Extract suggested follow-up questions from response."""
        # Simple extraction - in production, could use more sophisticated parsing
        suggestions = []
        
        # Look for questions in response
        import re
        questions = re.findall(r'[?]([^?]+)[?]', response)
        
        if questions:
            suggestions = [q.strip() + "?" for q in questions[:3]]
        
        return suggestions
    
    def get_conversation(self, conversation_id: UUID) -> ConversationContext | None:
        """Get conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def clear_conversation(self, conversation_id: UUID):
        """Clear conversation history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]


# Global instance
_conversational_query: ConversationalQuery | None = None


def get_conversational_query() -> ConversationalQuery:
    """Get conversational query instance."""
    global _conversational_query
    if _conversational_query is None:
        _conversational_query = ConversationalQuery()
    return _conversational_query
