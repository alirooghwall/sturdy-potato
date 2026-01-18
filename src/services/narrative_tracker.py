"""Narrative Tracking System for ISR Platform.

Tracks how narratives evolve over time, detecting narrative shifts,
amplification patterns, and cross-platform propagation.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from collections import defaultdict

import numpy as np


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class NarrativeStatus(str, Enum):
    """Status of tracked narrative."""
    EMERGING = "EMERGING"  # New narrative detected
    GROWING = "GROWING"  # Rapidly spreading
    STABLE = "STABLE"  # Consistent volume
    DECLINING = "DECLINING"  # Decreasing activity
    DORMANT = "DORMANT"  # Inactive
    RESURFACED = "RESURFACED"  # Reactivated after dormancy


class PropagationPattern(str, Enum):
    """How narrative spreads across platforms."""
    ORGANIC = "ORGANIC"  # Natural spread
    COORDINATED = "COORDINATED"  # Coordinated amplification
    BOT_DRIVEN = "BOT_DRIVEN"  # Bot network amplification
    INFLUENCER_LED = "INFLUENCER_LED"  # Driven by key accounts
    CROSS_PLATFORM = "CROSS_PLATFORM"  # Spreading across platforms


@dataclass
class NarrativeSnapshot:
    """Snapshot of narrative at a point in time."""
    snapshot_id: UUID
    narrative_id: UUID
    timestamp: datetime
    volume: int  # Number of mentions
    unique_sources: int  # Distinct sources
    platforms: list[str]  # Platforms where narrative appears
    sentiment_score: float  # Average sentiment
    coordination_score: float  # Coordination indicator
    geographic_spread: list[str]  # Regions/locations
    top_keywords: list[str]  # Most common keywords
    top_entities: list[str]  # Most mentioned entities
    engagement_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrativeEvolution:
    """Tracks how a narrative evolves over time."""
    evolution_id: UUID
    narrative_id: UUID
    narrative_name: str
    first_seen: datetime
    last_seen: datetime
    status: NarrativeStatus
    propagation_pattern: PropagationPattern
    snapshots: list[NarrativeSnapshot] = field(default_factory=list)
    total_volume: int = 0
    peak_volume: int = 0
    peak_timestamp: datetime | None = None
    growth_rate: float = 0.0  # Percent change per hour
    velocity: float = 0.0  # Spread speed across platforms
    acceleration: float = 0.0  # Change in growth rate
    mutation_events: list[dict[str, Any]] = field(default_factory=list)  # Narrative shifts
    key_amplifiers: list[str] = field(default_factory=list)  # Accounts driving spread
    related_narratives: list[UUID] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrativeMutation:
    """Detected change/mutation in narrative."""
    mutation_id: UUID
    narrative_id: UUID
    detected_at: datetime
    mutation_type: str  # FRAMING_SHIFT, TOPIC_PIVOT, SENTIMENT_FLIP, ESCALATION
    description: str
    before_keywords: list[str]
    after_keywords: list[str]
    before_sentiment: float
    after_sentiment: float
    confidence: float


@dataclass
class CrossPlatformTracker:
    """Tracks narrative spread across platforms."""
    tracker_id: UUID
    narrative_id: UUID
    origin_platform: str
    origin_timestamp: datetime
    spread_timeline: list[dict[str, Any]] = field(default_factory=list)
    platform_sequence: list[str] = field(default_factory=list)
    time_to_spread: dict[str, float] = field(default_factory=dict)  # Hours to reach each platform
    amplification_nodes: dict[str, list[str]] = field(default_factory=dict)  # Key accounts per platform


class NarrativeTracker:
    """Service for tracking narrative evolution over time."""

    def __init__(self):
        """Initialize narrative tracker."""
        self.tracked_narratives: dict[UUID, NarrativeEvolution] = {}
        self.narrative_by_name: dict[str, UUID] = {}
        self.mutations: dict[UUID, NarrativeMutation] = {}
        self.cross_platform_trackers: dict[UUID, CrossPlatformTracker] = {}
        
        # Time windows for analysis
        self.snapshot_interval_minutes = 30
        self.evolution_window_hours = 72
        
        # Thresholds
        self.emerging_threshold = 10  # Min volume to track
        self.viral_threshold = 1000  # Volume for viral classification
        self.coordination_threshold = 0.6  # Score for coordination detection
        
    def track_narrative(
        self,
        narrative_name: str,
        content: str,
        source_id: str,
        platform: str,
        timestamp: datetime,
        sentiment: float,
        entities: list[str],
        keywords: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> NarrativeEvolution:
        """Track a narrative occurrence."""
        metadata = metadata or {}
        
        # Get or create narrative evolution
        if narrative_name in self.narrative_by_name:
            narrative_id = self.narrative_by_name[narrative_name]
            evolution = self.tracked_narratives[narrative_id]
        else:
            # Create new tracked narrative
            narrative_id = uuid4()
            evolution = NarrativeEvolution(
                evolution_id=uuid4(),
                narrative_id=narrative_id,
                narrative_name=narrative_name,
                first_seen=timestamp,
                last_seen=timestamp,
                status=NarrativeStatus.EMERGING,
                propagation_pattern=PropagationPattern.ORGANIC,
            )
            self.tracked_narratives[narrative_id] = evolution
            self.narrative_by_name[narrative_name] = narrative_id
        
        # Update last seen
        evolution.last_seen = timestamp
        evolution.total_volume += 1
        
        # Check if we need a new snapshot
        self._update_or_create_snapshot(
            evolution,
            timestamp,
            platform,
            sentiment,
            entities,
            keywords,
            metadata,
        )
        
        # Update status and metrics
        self._update_narrative_metrics(evolution)
        
        # Detect mutations
        self._detect_mutations(evolution, keywords, sentiment, timestamp)
        
        # Track cross-platform spread
        self._track_cross_platform_spread(evolution, platform, timestamp)
        
        return evolution
    
    def _update_or_create_snapshot(
        self,
        evolution: NarrativeEvolution,
        timestamp: datetime,
        platform: str,
        sentiment: float,
        entities: list[str],
        keywords: list[str],
        metadata: dict[str, Any],
    ) -> None:
        """Update existing snapshot or create new one."""
        # Check if we need a new snapshot (based on time interval)
        if evolution.snapshots:
            last_snapshot = evolution.snapshots[-1]
            time_since_last = (timestamp - last_snapshot.timestamp).total_seconds() / 60
            
            if time_since_last < self.snapshot_interval_minutes:
                # Update existing snapshot
                last_snapshot.volume += 1
                last_snapshot.sentiment_score = (
                    (last_snapshot.sentiment_score * (last_snapshot.volume - 1) + sentiment)
                    / last_snapshot.volume
                )
                if platform not in last_snapshot.platforms:
                    last_snapshot.platforms.append(platform)
                
                # Update top keywords and entities
                last_snapshot.top_keywords = self._merge_top_items(
                    last_snapshot.top_keywords, keywords, limit=20
                )
                last_snapshot.top_entities = self._merge_top_items(
                    last_snapshot.top_entities, entities, limit=10
                )
                return
        
        # Create new snapshot
        snapshot = NarrativeSnapshot(
            snapshot_id=uuid4(),
            narrative_id=evolution.narrative_id,
            timestamp=timestamp,
            volume=1,
            unique_sources=1,
            platforms=[platform],
            sentiment_score=sentiment,
            coordination_score=metadata.get("coordination_score", 0.0),
            geographic_spread=metadata.get("locations", []),
            top_keywords=keywords[:20],
            top_entities=entities[:10],
            engagement_metrics=metadata.get("engagement", {}),
        )
        
        evolution.snapshots.append(snapshot)
    
    def _merge_top_items(
        self,
        existing: list[str],
        new: list[str],
        limit: int = 10,
    ) -> list[str]:
        """Merge and rank top items."""
        from collections import Counter
        
        all_items = existing + new
        counts = Counter(all_items)
        return [item for item, _ in counts.most_common(limit)]
    
    def _update_narrative_metrics(self, evolution: NarrativeEvolution) -> None:
        """Update narrative status and growth metrics."""
        if len(evolution.snapshots) < 2:
            return
        
        # Calculate growth rate
        recent_snapshots = evolution.snapshots[-10:]  # Last 10 snapshots
        if len(recent_snapshots) >= 2:
            volumes = [s.volume for s in recent_snapshots]
            time_range = (recent_snapshots[-1].timestamp - recent_snapshots[0].timestamp).total_seconds() / 3600
            
            if time_range > 0:
                volume_change = volumes[-1] - volumes[0]
                evolution.growth_rate = (volume_change / volumes[0]) * 100 / time_range if volumes[0] > 0 else 0
        
        # Update peak volume
        current_volume = evolution.snapshots[-1].volume
        if current_volume > evolution.peak_volume:
            evolution.peak_volume = current_volume
            evolution.peak_timestamp = evolution.snapshots[-1].timestamp
        
        # Calculate velocity (platforms per hour)
        if len(evolution.snapshots) >= 2:
            unique_platforms = set()
            for snapshot in evolution.snapshots:
                unique_platforms.update(snapshot.platforms)
            
            time_range = (evolution.last_seen - evolution.first_seen).total_seconds() / 3600
            if time_range > 0:
                evolution.velocity = len(unique_platforms) / time_range
        
        # Update status
        evolution.status = self._determine_status(evolution)
        
        # Detect propagation pattern
        evolution.propagation_pattern = self._detect_propagation_pattern(evolution)
    
    def _determine_status(self, evolution: NarrativeEvolution) -> NarrativeStatus:
        """Determine current status of narrative."""
        if len(evolution.snapshots) < 3:
            return NarrativeStatus.EMERGING
        
        # Check recent activity
        recent_snapshots = evolution.snapshots[-5:]
        volumes = [s.volume for s in recent_snapshots]
        
        # Calculate trend
        if len(volumes) >= 3:
            recent_avg = np.mean(volumes[-3:])
            earlier_avg = np.mean(volumes[:-3]) if len(volumes) > 3 else volumes[0]
            
            if recent_avg < 1:  # Very low activity
                # Check if it was previously active
                if evolution.peak_volume > 10:
                    return NarrativeStatus.DORMANT
                return NarrativeStatus.DECLINING
            
            if recent_avg > earlier_avg * 2:  # Doubling
                return NarrativeStatus.GROWING
            elif recent_avg < earlier_avg * 0.5:  # Halving
                return NarrativeStatus.DECLINING
            elif evolution.status == NarrativeStatus.DORMANT and recent_avg > 5:
                return NarrativeStatus.RESURFACED
            else:
                return NarrativeStatus.STABLE
        
        return NarrativeStatus.EMERGING
    
    def _detect_propagation_pattern(self, evolution: NarrativeEvolution) -> PropagationPattern:
        """Detect how narrative is spreading."""
        if len(evolution.snapshots) < 3:
            return PropagationPattern.ORGANIC
        
        recent_snapshots = evolution.snapshots[-10:]
        
        # Check coordination scores
        avg_coordination = np.mean([s.coordination_score for s in recent_snapshots])
        if avg_coordination > self.coordination_threshold:
            return PropagationPattern.COORDINATED
        
        # Check cross-platform spread
        platforms_count = len(set(
            p for s in recent_snapshots for p in s.platforms
        ))
        if platforms_count >= 3:
            return PropagationPattern.CROSS_PLATFORM
        
        # Check for rapid amplification
        if evolution.growth_rate > 200:  # 200% growth per hour
            # Could be bot-driven or influencer-led
            if avg_coordination > 0.4:
                return PropagationPattern.BOT_DRIVEN
            else:
                return PropagationPattern.INFLUENCER_LED
        
        return PropagationPattern.ORGANIC
    
    def _detect_mutations(
        self,
        evolution: NarrativeEvolution,
        keywords: list[str],
        sentiment: float,
        timestamp: datetime,
    ) -> None:
        """Detect if narrative has mutated/shifted."""
        if len(evolution.snapshots) < 5:
            return
        
        # Compare with earlier snapshots
        recent_snapshot = evolution.snapshots[-1]
        earlier_snapshot = evolution.snapshots[-5]
        
        # Check keyword shift
        recent_kw_set = set(recent_snapshot.top_keywords[:10])
        earlier_kw_set = set(earlier_snapshot.top_keywords[:10])
        
        overlap = len(recent_kw_set & earlier_kw_set)
        similarity = overlap / len(recent_kw_set) if recent_kw_set else 1.0
        
        # Check sentiment shift
        sentiment_change = abs(recent_snapshot.sentiment_score - earlier_snapshot.sentiment_score)
        
        mutation_type = None
        description = ""
        
        if similarity < 0.3:  # Major keyword shift
            mutation_type = "TOPIC_PIVOT"
            description = "Narrative focus has shifted significantly"
        elif sentiment_change > 0.5:  # Major sentiment change
            mutation_type = "SENTIMENT_FLIP"
            description = f"Sentiment shifted from {earlier_snapshot.sentiment_score:.2f} to {recent_snapshot.sentiment_score:.2f}"
        elif similarity < 0.6 and sentiment_change > 0.3:
            mutation_type = "FRAMING_SHIFT"
            description = "Narrative framing has changed"
        
        if mutation_type:
            mutation = NarrativeMutation(
                mutation_id=uuid4(),
                narrative_id=evolution.narrative_id,
                detected_at=timestamp,
                mutation_type=mutation_type,
                description=description,
                before_keywords=earlier_snapshot.top_keywords[:10],
                after_keywords=recent_snapshot.top_keywords[:10],
                before_sentiment=earlier_snapshot.sentiment_score,
                after_sentiment=recent_snapshot.sentiment_score,
                confidence=1.0 - similarity,
            )
            
            self.mutations[mutation.mutation_id] = mutation
            evolution.mutation_events.append({
                "mutation_id": str(mutation.mutation_id),
                "type": mutation_type,
                "timestamp": timestamp.isoformat(),
                "description": description,
            })
    
    def _track_cross_platform_spread(
        self,
        evolution: NarrativeEvolution,
        platform: str,
        timestamp: datetime,
    ) -> None:
        """Track how narrative spreads across platforms."""
        # Get or create cross-platform tracker
        tracker_id = evolution.narrative_id  # Use same ID for simplicity
        
        if tracker_id not in self.cross_platform_trackers:
            tracker = CrossPlatformTracker(
                tracker_id=tracker_id,
                narrative_id=evolution.narrative_id,
                origin_platform=platform,
                origin_timestamp=timestamp,
            )
            self.cross_platform_trackers[tracker_id] = tracker
        else:
            tracker = self.cross_platform_trackers[tracker_id]
        
        # Track new platform appearance
        if platform not in tracker.platform_sequence:
            tracker.platform_sequence.append(platform)
            
            # Calculate time to spread
            hours_to_spread = (timestamp - tracker.origin_timestamp).total_seconds() / 3600
            tracker.time_to_spread[platform] = hours_to_spread
            
            # Log spread event
            tracker.spread_timeline.append({
                "platform": platform,
                "timestamp": timestamp.isoformat(),
                "hours_from_origin": hours_to_spread,
            })
    
    def get_narrative_evolution(self, narrative_id: UUID) -> NarrativeEvolution | None:
        """Get evolution data for a narrative."""
        return self.tracked_narratives.get(narrative_id)
    
    def get_narrative_by_name(self, narrative_name: str) -> NarrativeEvolution | None:
        """Get narrative evolution by name."""
        narrative_id = self.narrative_by_name.get(narrative_name)
        if narrative_id:
            return self.tracked_narratives.get(narrative_id)
        return None
    
    def get_active_narratives(
        self,
        min_volume: int = 10,
        statuses: list[NarrativeStatus] | None = None,
    ) -> list[NarrativeEvolution]:
        """Get currently active narratives."""
        narratives = []
        
        for evolution in self.tracked_narratives.values():
            if evolution.total_volume < min_volume:
                continue
            
            if statuses and evolution.status not in statuses:
                continue
            
            # Check recent activity
            if evolution.snapshots:
                hours_since_last = (utcnow() - evolution.last_seen).total_seconds() / 3600
                if hours_since_last < self.evolution_window_hours:
                    narratives.append(evolution)
        
        # Sort by current momentum
        narratives.sort(key=lambda n: (n.growth_rate, n.total_volume), reverse=True)
        return narratives
    
    def get_emerging_narratives(self, limit: int = 10) -> list[NarrativeEvolution]:
        """Get emerging narratives to watch."""
        emerging = [
            n for n in self.tracked_narratives.values()
            if n.status in [NarrativeStatus.EMERGING, NarrativeStatus.GROWING]
            and n.growth_rate > 50  # Growing fast
        ]
        
        emerging.sort(key=lambda n: n.growth_rate, reverse=True)
        return emerging[:limit]
    
    def get_mutations(self, narrative_id: UUID) -> list[NarrativeMutation]:
        """Get detected mutations for a narrative."""
        return [
            m for m in self.mutations.values()
            if m.narrative_id == narrative_id
        ]
    
    def get_cross_platform_analysis(self, narrative_id: UUID) -> CrossPlatformTracker | None:
        """Get cross-platform spread analysis."""
        return self.cross_platform_trackers.get(narrative_id)
    
    def get_narrative_timeline(
        self,
        narrative_id: UUID,
        hours: int = 24,
    ) -> list[NarrativeSnapshot]:
        """Get narrative timeline for specified hours."""
        evolution = self.tracked_narratives.get(narrative_id)
        if not evolution:
            return []
        
        cutoff = utcnow() - timedelta(hours=hours)
        return [
            s for s in evolution.snapshots
            if s.timestamp >= cutoff
        ]
    
    def compare_narratives(
        self,
        narrative_id_1: UUID,
        narrative_id_2: UUID,
    ) -> dict[str, Any]:
        """Compare two narratives for similarities."""
        n1 = self.tracked_narratives.get(narrative_id_1)
        n2 = self.tracked_narratives.get(narrative_id_2)
        
        if not n1 or not n2:
            return {}
        
        # Get recent snapshots
        s1 = n1.snapshots[-1] if n1.snapshots else None
        s2 = n2.snapshots[-1] if n2.snapshots else None
        
        if not s1 or not s2:
            return {}
        
        # Calculate keyword overlap
        kw1 = set(s1.top_keywords[:20])
        kw2 = set(s2.top_keywords[:20])
        keyword_overlap = len(kw1 & kw2) / len(kw1 | kw2) if (kw1 | kw2) else 0
        
        # Calculate entity overlap
        e1 = set(s1.top_entities[:10])
        e2 = set(s2.top_entities[:10])
        entity_overlap = len(e1 & e2) / len(e1 | e2) if (e1 | e2) else 0
        
        # Platform overlap
        p1 = set(s1.platforms)
        p2 = set(s2.platforms)
        platform_overlap = len(p1 & p2) / len(p1 | p2) if (p1 | p2) else 0
        
        # Sentiment similarity
        sentiment_similarity = 1.0 - abs(s1.sentiment_score - s2.sentiment_score)
        
        # Overall similarity
        similarity = (
            keyword_overlap * 0.4 +
            entity_overlap * 0.3 +
            platform_overlap * 0.2 +
            sentiment_similarity * 0.1
        )
        
        return {
            "narrative_1": n1.narrative_name,
            "narrative_2": n2.narrative_name,
            "overall_similarity": similarity,
            "keyword_overlap": keyword_overlap,
            "entity_overlap": entity_overlap,
            "platform_overlap": platform_overlap,
            "sentiment_similarity": sentiment_similarity,
            "potentially_related": similarity > 0.6,
            "shared_keywords": list(kw1 & kw2),
            "shared_entities": list(e1 & e2),
            "shared_platforms": list(p1 & p2),
        }
    
    def get_stats(self) -> dict[str, Any]:
        """Get tracker statistics."""
        return {
            "total_narratives": len(self.tracked_narratives),
            "active_narratives": len(self.get_active_narratives()),
            "emerging_narratives": len(self.get_emerging_narratives()),
            "total_mutations": len(self.mutations),
            "cross_platform_tracks": len(self.cross_platform_trackers),
            "status_breakdown": {
                status.value: len([
                    n for n in self.tracked_narratives.values()
                    if n.status == status
                ])
                for status in NarrativeStatus
            },
        }


# Global instance
_narrative_tracker: NarrativeTracker | None = None


def get_narrative_tracker() -> NarrativeTracker:
    """Get the narrative tracker instance."""
    global _narrative_tracker
    if _narrative_tracker is None:
        _narrative_tracker = NarrativeTracker()
    return _narrative_tracker
