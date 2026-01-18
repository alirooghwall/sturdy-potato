"""Simulation Engine for ISR Platform.

Provides agent-based simulation, disaster modeling, and scenario replay
capabilities for Afghanistan ISR analysis.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import numpy as np


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class SimulationStatus(str, Enum):
    """Simulation lifecycle status."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SimulationType(str, Enum):
    """Types of simulations supported."""
    AGENT_BASED = "AGENT_BASED"
    DISASTER = "DISASTER"
    SCENARIO_REPLAY = "SCENARIO_REPLAY"
    WHAT_IF = "WHAT_IF"


class AgentType(str, Enum):
    """Types of agents in simulation."""
    CIVILIAN = "CIVILIAN"
    INSURGENT = "INSURGENT"
    MILITARY = "MILITARY"
    POLICE = "POLICE"
    HUMANITARIAN = "HUMANITARIAN"
    BORDER_PATROL = "BORDER_PATROL"


class DisasterType(str, Enum):
    """Types of disasters for modeling."""
    FLOOD = "FLOOD"
    EARTHQUAKE = "EARTHQUAKE"
    LANDSLIDE = "LANDSLIDE"
    DROUGHT = "DROUGHT"


@dataclass
class GeoCoordinate:
    """Geographic coordinate for simulation."""
    latitude: float
    longitude: float
    altitude: float = 0.0


@dataclass
class SimulationAgent:
    """Agent in the simulation."""
    agent_id: UUID
    agent_type: AgentType
    name: str
    position: GeoCoordinate
    velocity: tuple[float, float] = (0.0, 0.0)  # (speed_kmh, heading_degrees)
    attributes: dict[str, Any] = field(default_factory=dict)
    state: str = "ACTIVE"
    created_at: datetime = field(default_factory=utcnow)

    def move(self, dt_hours: float) -> None:
        """Move agent based on velocity for time delta."""
        if self.velocity[0] <= 0:
            return
        
        speed_kmh, heading_deg = self.velocity
        heading_rad = np.radians(heading_deg)
        
        # Simple movement model (approximate for small distances)
        distance_km = speed_kmh * dt_hours
        lat_delta = (distance_km / 111.0) * np.cos(heading_rad)
        lon_delta = (distance_km / (111.0 * np.cos(np.radians(self.position.latitude)))) * np.sin(heading_rad)
        
        self.position.latitude += lat_delta
        self.position.longitude += lon_delta


@dataclass
class DisasterEvent:
    """Disaster event in simulation."""
    event_id: UUID
    disaster_type: DisasterType
    epicenter: GeoCoordinate
    magnitude: float  # 0-10 scale
    radius_km: float
    start_time: datetime
    duration_hours: float
    casualties_estimate: int = 0
    infrastructure_damage_pct: float = 0.0
    population_affected: int = 0


@dataclass
class SimulationScenario:
    """Predefined scenario for replay or what-if analysis."""
    scenario_id: UUID
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    region: str
    initial_agents: list[dict[str, Any]] = field(default_factory=list)
    events_timeline: list[dict[str, Any]] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationState:
    """Current state of a simulation."""
    simulation_id: UUID
    simulation_type: SimulationType
    status: SimulationStatus
    name: str
    description: str = ""
    current_time: datetime = field(default_factory=utcnow)
    start_time: datetime = field(default_factory=utcnow)
    end_time: datetime | None = None
    time_step_minutes: int = 15
    agents: list[SimulationAgent] = field(default_factory=list)
    disasters: list[DisasterEvent] = field(default_factory=list)
    events_log: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


class SimulationEngine:
    """Engine for running ISR simulations."""

    def __init__(self) -> None:
        """Initialize simulation engine."""
        self.simulations: dict[UUID, SimulationState] = {}
        self.scenarios: dict[UUID, SimulationScenario] = {}
        self._load_default_scenarios()

    def _load_default_scenarios(self) -> None:
        """Load default scenarios from realistic Afghanistan data."""
        try:
            from src.data.scenarios import ALL_SCENARIOS
            
            for scenario_def in ALL_SCENARIOS.values():
                scenario = SimulationScenario(
                    scenario_id=uuid4(),
                    name=scenario_def.name,
                    description=scenario_def.description.strip(),
                    start_time=scenario_def.start_time,
                    end_time=scenario_def.end_time,
                    region=scenario_def.region,
                    initial_agents=scenario_def.initial_agents,
                    events_timeline=[
                        {"time_offset_hours": t.get("time_offset_hours", 0), "event": t.get("event", "")}
                        for t in scenario_def.triggers
                    ],
                    parameters={
                        **scenario_def.parameters,
                        "category": scenario_def.category,
                        "difficulty": scenario_def.difficulty,
                        "objectives": scenario_def.objectives,
                        "tags": scenario_def.tags,
                    },
                )
                self.scenarios[scenario.scenario_id] = scenario
        except ImportError:
            # Fallback to basic scenarios if data module not available
            self._load_fallback_scenarios()
    
    def _load_fallback_scenarios(self) -> None:
        """Load fallback scenarios if data module unavailable."""
        tora_bora = SimulationScenario(
            scenario_id=uuid4(),
            name="Tora Bora Operation (Historical)",
            description="Simulation of the December 2001 Tora Bora battle",
            start_time=datetime(2001, 12, 12, tzinfo=UTC),
            end_time=datetime(2001, 12, 17, tzinfo=UTC),
            region="Nangarhar Province",
            initial_agents=[
                {"type": "MILITARY", "count": 50, "position": {"lat": 34.1, "lon": 70.2}},
                {"type": "INSURGENT", "count": 100, "position": {"lat": 34.05, "lon": 70.15}},
            ],
            parameters={"terrain": "mountainous", "weather": "cold", "visibility": "limited"},
        )
        self.scenarios[tora_bora.scenario_id] = tora_bora

    def create_simulation(
        self,
        name: str,
        simulation_type: SimulationType,
        description: str = "",
        parameters: dict[str, Any] | None = None,
        scenario_id: UUID | None = None,
    ) -> SimulationState:
        """Create a new simulation."""
        simulation = SimulationState(
            simulation_id=uuid4(),
            simulation_type=simulation_type,
            status=SimulationStatus.CREATED,
            name=name,
            description=description,
            parameters=parameters or {},
        )

        # If scenario provided, initialize from it
        if scenario_id and scenario_id in self.scenarios:
            scenario = self.scenarios[scenario_id]
            simulation.current_time = scenario.start_time
            simulation.start_time = scenario.start_time
            simulation.end_time = scenario.end_time
            simulation.parameters.update(scenario.parameters)
            self._initialize_agents_from_scenario(simulation, scenario)

        self.simulations[simulation.simulation_id] = simulation
        return simulation

    def _initialize_agents_from_scenario(
        self,
        simulation: SimulationState,
        scenario: SimulationScenario,
    ) -> None:
        """Initialize agents from a scenario definition."""
        for agent_def in scenario.initial_agents:
            agent_type = AgentType(agent_def.get("type", "CIVILIAN"))
            count = agent_def.get("count", 1)
            base_pos = agent_def.get("position", {"lat": 34.5, "lon": 69.1})

            for i in range(count):
                # Add some randomness to positions
                lat_offset = np.random.uniform(-0.05, 0.05)
                lon_offset = np.random.uniform(-0.05, 0.05)

                agent = SimulationAgent(
                    agent_id=uuid4(),
                    agent_type=agent_type,
                    name=f"{agent_type.value}_{i+1}",
                    position=GeoCoordinate(
                        latitude=base_pos["lat"] + lat_offset,
                        longitude=base_pos["lon"] + lon_offset,
                    ),
                    attributes={"group": agent_def.get("group", "default")},
                )
                simulation.agents.append(agent)

    def start_simulation(self, simulation_id: UUID) -> SimulationState:
        """Start a simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        if simulation.status not in [SimulationStatus.CREATED, SimulationStatus.PAUSED]:
            raise ValueError(f"Cannot start simulation in {simulation.status} status")

        simulation.status = SimulationStatus.RUNNING
        simulation.updated_at = utcnow()
        return simulation

    def pause_simulation(self, simulation_id: UUID) -> SimulationState:
        """Pause a running simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        if simulation.status != SimulationStatus.RUNNING:
            raise ValueError("Can only pause running simulations")

        simulation.status = SimulationStatus.PAUSED
        simulation.updated_at = utcnow()
        return simulation

    def step_simulation(self, simulation_id: UUID, steps: int = 1) -> SimulationState:
        """Advance simulation by specified number of steps."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        if simulation.status != SimulationStatus.RUNNING:
            raise ValueError("Simulation must be running to step")

        dt_hours = simulation.time_step_minutes / 60.0

        for _ in range(steps):
            # Advance time
            simulation.current_time += timedelta(minutes=simulation.time_step_minutes)

            # Update agents
            self._update_agents(simulation, dt_hours)

            # Process disasters
            self._process_disasters(simulation)

            # Check for events
            self._check_events(simulation)

            # Update metrics
            self._update_metrics(simulation)

            # Check completion
            if simulation.end_time and simulation.current_time >= simulation.end_time:
                simulation.status = SimulationStatus.COMPLETED
                break

        simulation.updated_at = utcnow()
        return simulation

    def _update_agents(self, simulation: SimulationState, dt_hours: float) -> None:
        """Update all agents in simulation."""
        for agent in simulation.agents:
            if agent.state != "ACTIVE":
                continue

            # Simple random movement for demo
            if np.random.random() < 0.3:  # 30% chance to change direction
                agent.velocity = (
                    np.random.uniform(0, 20),  # 0-20 km/h
                    np.random.uniform(0, 360),  # Random heading
                )

            agent.move(dt_hours)

            # Log significant movements
            if agent.velocity[0] > 10:
                simulation.events_log.append({
                    "time": simulation.current_time.isoformat(),
                    "type": "AGENT_MOVEMENT",
                    "agent_id": str(agent.agent_id),
                    "agent_type": agent.agent_type.value,
                    "position": {
                        "lat": agent.position.latitude,
                        "lon": agent.position.longitude,
                    },
                })

    def _process_disasters(self, simulation: SimulationState) -> None:
        """Process active disasters and their effects."""
        for disaster in simulation.disasters:
            # Check if disaster is active
            disaster_end = disaster.start_time + timedelta(hours=disaster.duration_hours)
            if disaster.start_time <= simulation.current_time <= disaster_end:
                # Calculate effects on agents
                for agent in simulation.agents:
                    distance = self._calculate_distance(
                        disaster.epicenter,
                        agent.position,
                    )
                    if distance <= disaster.radius_km:
                        # Agent is affected
                        effect_strength = 1 - (distance / disaster.radius_km)
                        if np.random.random() < effect_strength * 0.1 * disaster.magnitude:
                            agent.state = "CASUALTY"
                            disaster.casualties_estimate += 1

    def _calculate_distance(self, pos1: GeoCoordinate, pos2: GeoCoordinate) -> float:
        """Calculate approximate distance between two coordinates in km."""
        lat_diff = pos2.latitude - pos1.latitude
        lon_diff = pos2.longitude - pos1.longitude
        # Simple approximation
        lat_km = lat_diff * 111.0
        lon_km = lon_diff * 111.0 * np.cos(np.radians(pos1.latitude))
        return np.sqrt(lat_km**2 + lon_km**2)

    def _check_events(self, simulation: SimulationState) -> None:
        """Check for and generate events based on simulation state."""
        # Check for agent encounters
        for i, agent1 in enumerate(simulation.agents):
            for agent2 in simulation.agents[i+1:]:
                if agent1.state != "ACTIVE" or agent2.state != "ACTIVE":
                    continue

                distance = self._calculate_distance(agent1.position, agent2.position)
                if distance < 1.0:  # Within 1km
                    # Check for hostile encounter
                    if self._is_hostile(agent1.agent_type, agent2.agent_type):
                        simulation.events_log.append({
                            "time": simulation.current_time.isoformat(),
                            "type": "HOSTILE_ENCOUNTER",
                            "agents": [str(agent1.agent_id), str(agent2.agent_id)],
                            "agent_types": [agent1.agent_type.value, agent2.agent_type.value],
                            "location": {
                                "lat": agent1.position.latitude,
                                "lon": agent1.position.longitude,
                            },
                        })

    def _is_hostile(self, type1: AgentType, type2: AgentType) -> bool:
        """Check if two agent types are hostile to each other."""
        hostile_pairs = [
            (AgentType.MILITARY, AgentType.INSURGENT),
            (AgentType.POLICE, AgentType.INSURGENT),
            (AgentType.BORDER_PATROL, AgentType.INSURGENT),
        ]
        return (type1, type2) in hostile_pairs or (type2, type1) in hostile_pairs

    def _update_metrics(self, simulation: SimulationState) -> None:
        """Update simulation metrics."""
        active_agents = [a for a in simulation.agents if a.state == "ACTIVE"]
        casualties = [a for a in simulation.agents if a.state == "CASUALTY"]

        agent_counts = {}
        for agent in active_agents:
            agent_counts[agent.agent_type.value] = agent_counts.get(agent.agent_type.value, 0) + 1

        simulation.metrics = {
            "total_agents": len(simulation.agents),
            "active_agents": len(active_agents),
            "casualties": len(casualties),
            "agent_breakdown": agent_counts,
            "events_count": len(simulation.events_log),
            "simulation_time": simulation.current_time.isoformat(),
            "steps_completed": int(
                (simulation.current_time - simulation.start_time).total_seconds()
                / (simulation.time_step_minutes * 60)
            ),
        }

    def add_disaster(
        self,
        simulation_id: UUID,
        disaster_type: DisasterType,
        epicenter_lat: float,
        epicenter_lon: float,
        magnitude: float,
        radius_km: float,
        duration_hours: float,
    ) -> DisasterEvent:
        """Add a disaster event to simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        disaster = DisasterEvent(
            event_id=uuid4(),
            disaster_type=disaster_type,
            epicenter=GeoCoordinate(latitude=epicenter_lat, longitude=epicenter_lon),
            magnitude=magnitude,
            radius_km=radius_km,
            start_time=simulation.current_time,
            duration_hours=duration_hours,
        )

        # Estimate affected population (simplified model)
        population_density = 100  # people per sq km (approximate)
        affected_area = np.pi * radius_km**2
        disaster.population_affected = int(affected_area * population_density * magnitude / 10)

        simulation.disasters.append(disaster)
        simulation.events_log.append({
            "time": simulation.current_time.isoformat(),
            "type": "DISASTER_START",
            "disaster_type": disaster_type.value,
            "magnitude": magnitude,
            "location": {"lat": epicenter_lat, "lon": epicenter_lon},
            "radius_km": radius_km,
            "estimated_affected": disaster.population_affected,
        })

        return disaster

    def add_agents(
        self,
        simulation_id: UUID,
        agent_type: AgentType,
        count: int,
        base_lat: float,
        base_lon: float,
        spread_km: float = 1.0,
    ) -> list[SimulationAgent]:
        """Add agents to simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        agents = []
        for i in range(count):
            # Random position within spread radius
            angle = np.random.uniform(0, 2 * np.pi)
            distance = np.random.uniform(0, spread_km)
            lat_offset = (distance / 111.0) * np.cos(angle)
            lon_offset = (distance / (111.0 * np.cos(np.radians(base_lat)))) * np.sin(angle)

            agent = SimulationAgent(
                agent_id=uuid4(),
                agent_type=agent_type,
                name=f"{agent_type.value}_{len(simulation.agents) + i + 1}",
                position=GeoCoordinate(
                    latitude=base_lat + lat_offset,
                    longitude=base_lon + lon_offset,
                ),
            )
            agents.append(agent)
            simulation.agents.append(agent)

        return agents

    def get_simulation(self, simulation_id: UUID) -> SimulationState | None:
        """Get simulation by ID."""
        return self.simulations.get(simulation_id)

    def list_simulations(self) -> list[SimulationState]:
        """List all simulations."""
        return list(self.simulations.values())

    def list_scenarios(self) -> list[SimulationScenario]:
        """List available scenarios."""
        return list(self.scenarios.values())

    def get_scenario(self, scenario_id: UUID) -> SimulationScenario | None:
        """Get scenario by ID."""
        return self.scenarios.get(scenario_id)

    def cancel_simulation(self, simulation_id: UUID) -> SimulationState:
        """Cancel a simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {simulation_id} not found")

        simulation.status = SimulationStatus.CANCELLED
        simulation.updated_at = utcnow()
        return simulation


# Global instance
_simulation_engine: SimulationEngine | None = None


def get_simulation_engine() -> SimulationEngine:
    """Get the simulation engine instance."""
    global _simulation_engine
    if _simulation_engine is None:
        _simulation_engine = SimulationEngine()
    return _simulation_engine
