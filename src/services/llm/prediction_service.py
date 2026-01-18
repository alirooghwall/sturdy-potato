"""Prediction and forecasting service using LLM + statistical models."""

import logging
from typing import Any
from uuid import uuid4
from datetime import datetime, timedelta

import numpy as np

from .llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


class PredictionService:
    """Generate predictions and forecasts for intelligence scenarios."""
    
    def __init__(self, llm_service: LLMService | None = None):
        """Initialize prediction service.
        
        Args:
            llm_service: LLM service instance
        """
        self.llm = llm_service or get_llm_service()
        self.predictions: dict[str, dict[str, Any]] = {}
    
    async def predict_narrative_evolution(
        self,
        narrative_data: dict[str, Any],
        time_horizon_hours: int = 48,
    ) -> dict[str, Any]:
        """Predict how a narrative will evolve.
        
        Combines statistical trends with LLM reasoning.
        
        Args:
            narrative_data: Current narrative state
            time_horizon_hours: How far ahead to predict
        
        Returns:
            Prediction with confidence bands
        """
        # Statistical prediction
        historical_volume = narrative_data.get('historical_volume', [])
        growth_rate = narrative_data.get('growth_rate', 0)
        
        # Simple exponential extrapolation
        current_volume = narrative_data.get('total_volume', 0)
        predicted_volume = current_volume * ((1 + growth_rate/100) ** (time_horizon_hours / 24))
        
        system_prompt = """You are a predictive analyst specializing in information warfare and narrative dynamics.
Predict how narratives will evolve based on current trends, historical patterns, and contextual factors."""
        
        prompt = f"""Predict narrative evolution for the next {time_horizon_hours} hours:

Narrative: {narrative_data.get('name')}
Current Status: {narrative_data.get('status')}
Current Volume: {current_volume} mentions
Growth Rate: {growth_rate:.2f}%/hour
Propagation Pattern: {narrative_data.get('propagation_pattern')}
Platforms: {narrative_data.get('platforms', [])}

Statistical Prediction: {predicted_volume:.0f} mentions

Analyze and predict:
1. Likely trajectory (VIRAL, STABLE, DECLINING)
2. Platform spread pattern
3. Potential mutations or framing shifts
4. Peak timing estimate
5. Confidence in predictions
6. Key factors that could change trajectory
7. Recommended interventions"""
        
        try:
            llm_analysis = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=1500,
            )
            
            return {
                "prediction_id": str(uuid4()),
                "narrative": narrative_data.get('name'),
                "prediction_type": "narrative_evolution",
                "time_horizon_hours": time_horizon_hours,
                "generated_at": datetime.utcnow().isoformat(),
                "statistical_prediction": {
                    "predicted_volume": float(predicted_volume),
                    "method": "exponential_growth",
                    "current_volume": current_volume,
                    "growth_rate": growth_rate,
                },
                "llm_analysis": llm_analysis,
                "confidence": 0.7,
            }
        
        except Exception as e:
            logger.error(f"Narrative prediction error: {e}")
            raise
    
    async def predict_event_likelihood(
        self,
        event_type: str,
        current_indicators: dict[str, Any],
        historical_precedents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Predict likelihood of specific event occurring.
        
        Args:
            event_type: Type of event to predict
            current_indicators: Current warning indicators
            historical_precedents: Similar past events
        
        Returns:
            Likelihood assessment with reasoning
        """
        system_prompt = """You are a predictive intelligence analyst assessing event probabilities.
Use indicator analysis, pattern matching, and reasoning to estimate likelihoods.
Provide probabilistic assessments with clear reasoning."""
        
        prompt = f"""Assess likelihood of: {event_type}

Current Indicators:
{self._format_indicators(current_indicators)}

Historical Precedents: {len(historical_precedents)} similar cases
{self._summarize_precedents(historical_precedents[:5])}

Assess:
1. Probability (percentage and confidence interval)
2. Key indicators present
3. Missing indicators
4. Comparison to historical patterns
5. Timeline estimate (if likely)
6. Early warning signs to watch
7. Actions to reduce likelihood (if threat)"""
        
        try:
            assessment = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=1500,
            )
            
            return {
                "prediction_id": str(uuid4()),
                "event_type": event_type,
                "generated_at": datetime.utcnow().isoformat(),
                "assessment": assessment,
                "indicators": current_indicators,
                "historical_sample_size": len(historical_precedents),
            }
        
        except Exception as e:
            logger.error(f"Event likelihood error: {e}")
            raise
    
    async def forecast_environmental_impact(
        self,
        satellite_trend: dict[str, Any],
        forecast_months: int = 6,
    ) -> dict[str, Any]:
        """Forecast environmental impacts based on satellite trends.
        
        Args:
            satellite_trend: Long-term satellite trend data
            forecast_months: Months to forecast ahead
        
        Returns:
            Environmental impact forecast
        """
        system_prompt = """You are an environmental scientist and forecaster.
Predict future environmental conditions and impacts based on current trends.
Consider climate factors, human activities, and feedback loops."""
        
        # Statistical forecast
        data_points = satellite_trend.get('data_points', [])
        if len(data_points) >= 3:
            values = [p.get('value', 0) for p in data_points]
            x = np.arange(len(values))
            z = np.polyfit(x, values, 1)
            
            # Extrapolate
            future_months = forecast_months
            future_x = len(values) + (future_months * 30 / (len(values) / len(data_points)))
            predicted_value = np.poly1d(z)(future_x)
        else:
            predicted_value = 0
        
        prompt = f"""Forecast environmental impact for next {forecast_months} months:

Analysis Type: {satellite_trend.get('analysis_type')}
Location: {satellite_trend.get('location')}
Current Trend: {satellite_trend.get('trend_direction')}
Rate of Change: {satellite_trend.get('rate_of_change')}/year

Historical Data Points: {len(data_points)}
Statistical Forecast: {predicted_value:.3f}

Current Conditions:
{self._format_dict(satellite_trend.get('current_conditions', {}))}

Forecast:
1. Expected conditions in {forecast_months} months
2. Confidence level and uncertainty
3. Best case / worst case scenarios
4. Tipping points or thresholds
5. Environmental impacts
6. Social/economic impacts
7. Mitigation recommendations"""
        
        try:
            forecast = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=1800,
            )
            
            return {
                "forecast_id": str(uuid4()),
                "analysis_type": satellite_trend.get('analysis_type'),
                "forecast_months": forecast_months,
                "generated_at": datetime.utcnow().isoformat(),
                "statistical_forecast": float(predicted_value),
                "llm_forecast": forecast,
                "confidence": 0.65,
            }
        
        except Exception as e:
            logger.error(f"Environmental forecast error: {e}")
            raise
    
    async def generate_scenario_analysis(
        self,
        current_situation: dict[str, Any],
        what_if_conditions: list[str],
    ) -> dict[str, Any]:
        """Generate 'what-if' scenario analysis.
        
        Creative feature for strategic planning.
        
        Args:
            current_situation: Current intelligence picture
            what_if_conditions: Hypothetical conditions to analyze
        
        Returns:
            Scenario analysis with outcomes
        """
        system_prompt = """You are a strategic planner conducting scenario analysis.
Evaluate how different conditions would affect outcomes.
Consider second-order effects, cascading impacts, and strategic implications."""
        
        scenarios_str = "\n".join([f"{i+1}. {cond}" for i, cond in enumerate(what_if_conditions)])
        
        prompt = f"""Conduct scenario analysis:

CURRENT SITUATION:
{self._format_dict(current_situation)}

WHAT-IF SCENARIOS:
{scenarios_str}

For each scenario, analyze:
1. Immediate effects
2. Second-order consequences
3. Probability of occurrence
4. Impact severity (if occurs)
5. Mitigation strategies
6. Indicators to watch

Provide strategic assessment for decision-making."""
        
        try:
            analysis = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000,
            )
            
            return {
                "analysis_id": str(uuid4()),
                "generated_at": datetime.utcnow().isoformat(),
                "scenarios_analyzed": len(what_if_conditions),
                "analysis": analysis,
                "current_situation": current_situation,
                "what_if_conditions": what_if_conditions,
            }
        
        except Exception as e:
            logger.error(f"Scenario analysis error: {e}")
            raise
    
    def _format_indicators(self, indicators: dict[str, Any]) -> str:
        """Format indicators for prompt."""
        return "\n".join([
            f"- {k}: {v} {'✓ Present' if v else '✗ Absent'}"
            if isinstance(v, bool)
            else f"- {k}: {v}"
            for k, v in indicators.items()
        ])
    
    def _summarize_precedents(self, precedents: list[dict[str, Any]]) -> str:
        """Summarize historical precedents."""
        if not precedents:
            return "No precedents"
        
        summary = []
        for prec in precedents:
            summary.append(
                f"- {prec.get('date')}: {prec.get('description', '')[:60]} "
                f"(Outcome: {prec.get('outcome', 'N/A')})"
            )
        return "\n".join(summary)
    
    def _format_dict(self, data: dict[str, Any]) -> str:
        """Format dictionary for prompt."""
        return "\n".join([f"- {k}: {v}" for k, v in data.items()])


# Global instance
_prediction_service: PredictionService | None = None


def get_prediction_service() -> PredictionService:
    """Get prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
