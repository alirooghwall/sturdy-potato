"""Base connector class for data ingestion.

Provides common functionality for all data source connectors:
- Rate limiting
- Retry logic with exponential backoff
- Circuit breaker pattern
- Health monitoring
- Error handling
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)

T = TypeVar('T')


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class ConnectorStatus(str, Enum):
    """Connector health status."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    DISABLED = "DISABLED"


@dataclass
class ConnectorConfig:
    """Configuration for a data connector."""
    name: str
    enabled: bool = True
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_requests_per_day: int = 10000
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: int = 1
    retry_backoff_factor: float = 2.0
    
    # Circuit breaker
    circuit_breaker_threshold: int = 5  # failures before opening
    circuit_breaker_timeout: int = 60  # seconds before retry
    
    # Timeouts
    connection_timeout: int = 10
    read_timeout: int = 30
    
    # Polling
    poll_interval_seconds: int = 300  # 5 minutes default


@dataclass
class RateLimiter:
    """Token bucket rate limiter."""
    max_per_minute: int
    max_per_hour: int
    max_per_day: int
    
    _minute_tokens: int = field(init=False)
    _hour_tokens: int = field(init=False)
    _day_tokens: int = field(init=False)
    _last_minute_reset: datetime = field(default_factory=utcnow, init=False)
    _last_hour_reset: datetime = field(default_factory=utcnow, init=False)
    _last_day_reset: datetime = field(default_factory=utcnow, init=False)
    
    def __post_init__(self):
        self._minute_tokens = self.max_per_minute
        self._hour_tokens = self.max_per_hour
        self._day_tokens = self.max_per_day
    
    def _reset_if_needed(self) -> None:
        """Reset token buckets if time windows have passed."""
        now = utcnow()
        
        # Reset minute bucket
        if now - self._last_minute_reset >= timedelta(minutes=1):
            self._minute_tokens = self.max_per_minute
            self._last_minute_reset = now
        
        # Reset hour bucket
        if now - self._last_hour_reset >= timedelta(hours=1):
            self._hour_tokens = self.max_per_hour
            self._last_hour_reset = now
        
        # Reset day bucket
        if now - self._last_day_reset >= timedelta(days=1):
            self._day_tokens = self.max_per_day
            self._last_day_reset = now
    
    async def acquire(self) -> bool:
        """Acquire a token, returns True if successful."""
        self._reset_if_needed()
        
        if self._minute_tokens > 0 and self._hour_tokens > 0 and self._day_tokens > 0:
            self._minute_tokens -= 1
            self._hour_tokens -= 1
            self._day_tokens -= 1
            return True
        
        return False
    
    def get_wait_time(self) -> float:
        """Get estimated wait time in seconds."""
        self._reset_if_needed()
        
        now = utcnow()
        
        if self._minute_tokens <= 0:
            return (self._last_minute_reset + timedelta(minutes=1) - now).total_seconds()
        elif self._hour_tokens <= 0:
            return (self._last_hour_reset + timedelta(hours=1) - now).total_seconds()
        elif self._day_tokens <= 0:
            return (self._last_day_reset + timedelta(days=1) - now).total_seconds()
        
        return 0.0


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    threshold: int
    timeout_seconds: int
    
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: datetime | None = field(default=None, init=False)
    _state: str = field(default="CLOSED", init=False)  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self) -> None:
        """Record a successful operation."""
        self._failure_count = 0
        self._state = "CLOSED"
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        self._failure_count += 1
        self._last_failure_time = utcnow()
        
        if self._failure_count >= self.threshold:
            self._state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )
    
    def can_attempt(self) -> bool:
        """Check if we can attempt an operation."""
        if self._state == "CLOSED":
            return True
        
        if self._state == "OPEN":
            # Check if timeout has passed
            if self._last_failure_time:
                elapsed = (utcnow() - self._last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    self._state = "HALF_OPEN"
                    logger.info("Circuit breaker entering HALF_OPEN state")
                    return True
            return False
        
        # HALF_OPEN state - allow one attempt
        return True
    
    @property
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self._state == "OPEN"


class BaseConnector(ABC, Generic[T]):
    """Base class for all data source connectors.
    
    Provides:
    - Automatic rate limiting
    - Retry logic with exponential backoff
    - Circuit breaker pattern
    - Health monitoring
    - Graceful error handling
    """

    def __init__(self, config: ConnectorConfig):
        """Initialize connector."""
        self.config = config
        self.connector_id = str(uuid4())
        
        # HTTP client
        self._client: httpx.AsyncClient | None = None
        
        # Rate limiting
        self._rate_limiter = RateLimiter(
            max_per_minute=config.max_requests_per_minute,
            max_per_hour=config.max_requests_per_hour,
            max_per_day=config.max_requests_per_day,
        )
        
        # Circuit breaker
        self._circuit_breaker = CircuitBreaker(
            threshold=config.circuit_breaker_threshold,
            timeout_seconds=config.circuit_breaker_timeout,
        )
        
        # State
        self._status = ConnectorStatus.HEALTHY
        self._running = False
        self._poll_task: asyncio.Task | None = None
        
        # Statistics
        self._stats = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "records_ingested": 0,
            "last_success": None,
            "last_error": None,
        }
    
    async def start(self) -> None:
        """Start the connector."""
        if not self.config.enabled:
            logger.info(f"Connector {self.config.name} is disabled")
            self._status = ConnectorStatus.DISABLED
            return
        
        if self._running:
            return
        
        logger.info(f"Starting connector: {self.config.name}")
        
        # Initialize HTTP client
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=self.config.connection_timeout,
                read=self.config.read_timeout,
            ),
            follow_redirects=True,
        )
        
        # Start polling task
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        
        logger.info(f"✓ Connector started: {self.config.name}")
    
    async def stop(self) -> None:
        """Stop the connector."""
        if not self._running:
            return
        
        logger.info(f"Stopping connector: {self.config.name}")
        
        self._running = False
        
        # Cancel polling task
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP client
        if self._client:
            await self._client.aclose()
        
        logger.info(f"✓ Connector stopped: {self.config.name}")
    
    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in poll loop for {self.config.name}: {e}")
                self._stats["requests_failed"] += 1
                self._stats["last_error"] = str(e)
            
            # Wait before next poll
            await asyncio.sleep(self.config.poll_interval_seconds)
    
    async def _poll_once(self) -> None:
        """Execute one polling cycle."""
        if not self._circuit_breaker.can_attempt():
            logger.warning(
                f"Circuit breaker open for {self.config.name}, skipping poll"
            )
            self._status = ConnectorStatus.UNHEALTHY
            return
        
        # Wait for rate limit
        while not await self._rate_limiter.acquire():
            wait_time = self._rate_limiter.get_wait_time()
            logger.warning(
                f"Rate limit reached for {self.config.name}, waiting {wait_time:.1f}s"
            )
            await asyncio.sleep(min(wait_time, 60))
        
        try:
            # Fetch data with retry logic
            data = await self._fetch_with_retry()
            
            if data:
                # Process and ingest data
                await self.ingest_data(data)
                
                self._stats["requests_successful"] += 1
                self._stats["records_ingested"] += len(data) if isinstance(data, list) else 1
                self._stats["last_success"] = utcnow().isoformat()
                
                self._circuit_breaker.record_success()
                self._status = ConnectorStatus.HEALTHY
                
                logger.debug(f"Successfully polled {self.config.name}")
        
        except Exception as e:
            logger.error(f"Error polling {self.config.name}: {e}")
            self._stats["requests_failed"] += 1
            self._stats["last_error"] = str(e)
            
            self._circuit_breaker.record_failure()
            self._status = ConnectorStatus.DEGRADED
    
    async def _fetch_with_retry(self) -> T | None:
        """Fetch data with exponential backoff retry."""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                self._stats["requests_total"] += 1
                return await self.fetch_data()
            
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{self.config.max_retries} "
                    f"for {self.config.name}"
                )
            
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code >= 500:
                    # Server error - retry
                    logger.warning(
                        f"Server error {e.response.status_code} on attempt "
                        f"{attempt + 1}/{self.config.max_retries} for {self.config.name}"
                    )
                elif e.response.status_code == 429:
                    # Rate limited - wait longer
                    logger.warning(f"Rate limited by {self.config.name}, backing off")
                    await asyncio.sleep(60)
                    continue
                else:
                    # Client error - don't retry
                    raise
            
            except Exception as e:
                last_error = e
                logger.error(
                    f"Error on attempt {attempt + 1}/{self.config.max_retries} "
                    f"for {self.config.name}: {e}"
                )
            
            # Exponential backoff
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay_seconds * (
                    self.config.retry_backoff_factor ** attempt
                )
                await asyncio.sleep(delay)
        
        # All retries failed
        if last_error:
            raise last_error
        
        return None
    
    @abstractmethod
    async def fetch_data(self) -> T | None:
        """Fetch data from the source.
        
        Must be implemented by subclasses.
        Returns the raw data from the source.
        """
        pass
    
    @abstractmethod
    async def ingest_data(self, data: T) -> None:
        """Process and ingest data into the system.
        
        Must be implemented by subclasses.
        Should publish data to Kafka topics.
        """
        pass
    
    def get_status(self) -> dict[str, Any]:
        """Get connector status and statistics."""
        return {
            "connector_id": self.connector_id,
            "name": self.config.name,
            "enabled": self.config.enabled,
            "status": self._status.value,
            "running": self._running,
            "circuit_breaker": {
                "state": self._circuit_breaker._state,
                "is_open": self._circuit_breaker.is_open,
                "failure_count": self._circuit_breaker._failure_count,
            },
            "stats": self._stats,
        }
