"""Core LLM service with multi-provider support."""

import logging
from enum import Enum
from typing import Any, AsyncGenerator
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider
    api_key: str | None = None
    api_base: str | None = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60


class LLMService:
    """Universal LLM service supporting multiple providers."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM service.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)
        
        # Set provider-specific defaults
        if config.provider == LLMProvider.OPENAI:
            self.api_base = config.api_base or "https://api.openai.com/v1"
            self.default_model = config.model or "gpt-4"
        
        elif config.provider == LLMProvider.ANTHROPIC:
            self.api_base = config.api_base or "https://api.anthropic.com/v1"
            self.default_model = config.model or "claude-3-opus-20240229"
        
        elif config.provider == LLMProvider.AZURE_OPENAI:
            # Azure requires custom endpoint
            self.api_base = config.api_base
            self.default_model = config.model
        
        elif config.provider == LLMProvider.OLLAMA:
            self.api_base = config.api_base or "http://localhost:11434/api"
            self.default_model = config.model or "llama2"
        
        else:
            self.api_base = config.api_base
            self.default_model = config.model
        
        logger.info(f"LLM service initialized with provider: {config.provider}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> str:
        """Generate text completion.
        
        Args:
            prompt: User prompt
            system_prompt: System/instruction prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Generated text
        """
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        if self.config.provider == LLMProvider.OPENAI:
            return await self._generate_openai(prompt, system_prompt, temperature, max_tokens, **kwargs)
        
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return await self._generate_anthropic(prompt, system_prompt, temperature, max_tokens, **kwargs)
        
        elif self.config.provider == LLMProvider.OLLAMA:
            return await self._generate_ollama(prompt, system_prompt, temperature, max_tokens, **kwargs)
        
        else:
            raise NotImplementedError(f"Provider {self.config.provider} not implemented")
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate text completion with streaming.
        
        Args:
            prompt: User prompt
            system_prompt: System/instruction prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Text chunks as they're generated
        """
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        if self.config.provider == LLMProvider.OPENAI:
            async for chunk in self._generate_openai_stream(prompt, system_prompt, temperature, max_tokens, **kwargs):
                yield chunk
        
        elif self.config.provider == LLMProvider.ANTHROPIC:
            async for chunk in self._generate_anthropic_stream(prompt, system_prompt, temperature, max_tokens, **kwargs):
                yield chunk
        
        else:
            # Fallback to non-streaming
            result = await self.generate(prompt, system_prompt, temperature, max_tokens, **kwargs)
            yield result
    
    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> str:
        """Generate using OpenAI API."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs,
                },
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def _generate_openai_stream(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate using OpenAI API with streaming."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                    **kwargs,
                },
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            import json
                            data = json.loads(data_str)
                            
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    yield content
                        
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
    
    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> str:
        """Generate using Anthropic Claude API."""
        try:
            payload = {
                "model": self.default_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await self.client.post(
                f"{self.api_base}/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data["content"][0]["text"]
        
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise
    
    async def _generate_anthropic_stream(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate using Anthropic Claude API with streaming."""
        try:
            payload = {
                "model": self.default_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": True,
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            async with self.client.stream(
                "POST",
                f"{self.api_base}/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        data = json.loads(line[6:])
                        
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            text = delta.get("text", "")
                            
                            if text:
                                yield text
        
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> str:
        """Generate using Ollama local API."""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = await self.client.post(
                f"{self.api_base}/generate",
                json={
                    "model": self.default_model,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "options": {
                        "num_predict": max_tokens,
                    },
                },
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", "")
        
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    global _llm_service
    
    if _llm_service is None:
        # Try to load from environment
        import os
        
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        provider_str = os.getenv("LLM_PROVIDER", "openai")
        model = os.getenv("LLM_MODEL", "gpt-4")
        
        try:
            provider = LLMProvider(provider_str.lower())
        except ValueError:
            provider = LLMProvider.OPENAI
        
        config = LLMConfig(
            provider=provider,
            api_key=api_key,
            model=model,
        )
        
        _llm_service = LLMService(config)
    
    return _llm_service


def set_llm_service(service: LLMService):
    """Set custom LLM service instance."""
    global _llm_service
    _llm_service = service
