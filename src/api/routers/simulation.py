"""Simulation engine endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.services.simulation_engine import (
    AgentType,
    DisasterType,
    SimulationStatus,
    SimulationType,
    get_simulation_engine,
)

from .auth import require_permission


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Request/Response schemas
class CreateSimulationRequest(BaseModel):
    """Request to create a simulation."""
    name: str
    simulation_type: SimulationType
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    scenario_id: UUID | None = None


class AddAgentsRequest(BaseModel):
    """Request to add agents to simulation."""
    agent_type: AgentType
    count: int = Field(ge=1, le=1000)
    base_latitude: float = Field(ge=-90, le=90)
    base_longitude: float = Field(ge=-180, le=180)
    spread_km: float = Field(default=1.0, ge=0.1, le=100)


class AddDisasterRequest(BaseModel):
    """Request to add disaster to simulation."""
    disaster_type: DisasterType
    epicenter_latitude: float = Field(ge=-90, le=90)
    epicenter_longitude: float = Field(ge=-180, le=180)
    magnitude: float = Field(ge=1, le=10)
    radius_km: float = Field(ge=1, le=500)
    duration_hours: float = Field(ge=1, le=720)


class SimulationResponse(BaseModel):
    """Response for simulation operations."""
    simulation_id: UUID
    name: str
    simulation_type: str
    status: str
    current_time: str
    agent_count: int
    disaster_count: int
    events_count: int
    metrics: dict[str, Any]
    created_at: str
    updated_at: str


class ScenarioResponse(BaseModel):
    """Response for scenario listing."""
    scenario_id: UUID
    name: str
    description: str
    region: str
    start_time: str
    end_time: str


def _simulation_to_response(sim) -> SimulationResponse:
    """Convert simulation state to response."""
    return SimulationResponse(
        simulation_id=sim.simulation_id,
        name=sim.name,
        simulation_type=sim.simulation_type.value,
        status=sim.status.value,
        current_time=sim.current_time.isoformat(),
        agent_count=len(sim.agents),
        disaster_count=len(sim.disasters),
        events_count=len(sim.events_log),
        metrics=sim.metrics,
        created_at=sim.created_at.isoformat(),
        updated_at=sim.updated_at.isoformat(),
    )


@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    request: CreateSimulationRequest,
    user: Annotated[dict, Depends(require_permission("simulation:create"))],
) -> SimulationResponse:
    """Create a new simulation."""
    engine = get_simulation_engine()

    simulation = engine.create_simulation(
        name=request.name,
        simulation_type=request.simulation_type,
        description=request.description,
        parameters=request.parameters,
        scenario_id=request.scenario_id,
    )

    return _simulation_to_response(simulation)


@router.get("", response_model=list[SimulationResponse])
async def list_simulations(
    user: Annotated[dict, Depends(require_permission("simulation:read"))],
    status_filter: SimulationStatus | None = Query(default=None, alias="status"),
) -> list[SimulationResponse]:
    """List all simulations."""
    engine = get_simulation_engine()
    simulations = engine.list_simulations()

    if status_filter:
        simulations = [s for s in simulations if s.status == status_filter]

    return [_simulation_to_response(s) for s in simulations]


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios(
    user: Annotated[dict, Depends(require_permission("simulation:read"))],
) -> list[ScenarioResponse]:
    """List available simulation scenarios."""
    engine = get_simulation_engine()
    scenarios = engine.list_scenarios()

    return [
        ScenarioResponse(
            scenario_id=s.scenario_id,
            name=s.name,
            description=s.description,
            region=s.region,
            start_time=s.start_time.isoformat(),
            end_time=s.end_time.isoformat(),
        )
        for s in scenarios
    ]


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: UUID,
    user: Annotated[dict, Depends(require_permission("simulation:read"))],
) -> SimulationResponse:
    """Get simulation by ID."""
    engine = get_simulation_engine()
    simulation = engine.get_simulation(simulation_id)

    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    return _simulation_to_response(simulation)


@router.post("/{simulation_id}/start", response_model=SimulationResponse)
async def start_simulation(
    simulation_id: UUID,
    user: Annotated[dict, Depends(require_permission("simulation:run"))],
) -> SimulationResponse:
    """Start a simulation."""
    engine = get_simulation_engine()

    try:
        simulation = engine.start_simulation(simulation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _simulation_to_response(simulation)


@router.post("/{simulation_id}/pause", response_model=SimulationResponse)
async def pause_simulation(
    simulation_id: UUID,
    user: Annotated[dict, Depends(require_permission("simulation:run"))],
) -> SimulationResponse:
    """Pause a running simulation."""
    engine = get_simulation_engine()

    try:
        simulation = engine.pause_simulation(simulation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _simulation_to_response(simulation)


@router.post("/{simulation_id}/step", response_model=SimulationResponse)
async def step_simulation(
    simulation_id: UUID,
    user: Annotated[dict, Depends(require_permission("simulation:run"))],
    steps: int = Query(default=1, ge=1, le=100),
) -> SimulationResponse:
    """Advance simulation by specified steps."""
    engine = get_simulation_engine()

    try:
        simulation = engine.step_simulation(simulation_id, steps)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _simulation_to_response(simulation)


@router.post("/{simulation_id}/cancel", response_model=SimulationResponse)
async def cancel_simulation(
    simulation_id: UUID,
    user: Annotated[dict, Depends(require_permission("simulation:run"))],
) -> SimulationResponse:
    """Cancel a simulation."""
    engine = get_simulation_engine()

    try:
        simulation = engine.cancel_simulation(simulation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _simulation_to_response(simulation)


@router.post("/{simulation_id}/agents")
async def add_agents(
    simulation_id: UUID,
    request: AddAgentsRequest,
    user: Annotated[dict, Depends(require_permission("simulation:run"))],
) -> dict[str, Any]:
    """Add agents to simulation."""
    engine = get_simulation_engine()

    try:
        agents = engine.add_agents(
            simulation_id=simulation_id,
            agent_type=request.agent_type,
            count=request.count,
            base_lat=request.base_latitude,
            base_lon=request.base_longitude,
            spread_km=request.spread_km,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return {
        "message": f"Added {len(agents)} agents to simulation",
        "agent_ids": [str(a.agent_id) for a in agents],
        "agent_type": request.agent_type.value,
        "timestamp": utcnow().isoformat(),
    }


@router.post("/{simulation_id}/disasters")
async def add_disaster(
    simulation_id: UUID,
    request: AddDisasterRequest,
    user: Annotated[dict, Depends(require_permission("simulation:run"))],
) -> dict[str, Any]:
    """Add disaster event to simulation."""
    engine = get_simulation_engine()

    try:
        disaster = engine.add_disaster(
            simulation_id=simulation_id,
            disaster_type=request.disaster_type,
            epicenter_lat=request.epicenter_latitude,
            epicenter_lon=request.epicenter_longitude,
            magnitude=request.magnitude,
            radius_km=request.radius_km,
            duration_hours=request.duration_hours,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return {
        "message": "Disaster added to simulation",
        "disaster_id": str(disaster.event_id),
        "disaster_type": disaster.disaster_type.value,
        "magnitude": disaster.magnitude,
        "estimated_affected": disaster.population_affected,
        "timestamp": utcnow().isoformat(),
    }


@router.get("/{simulation_id}/events")
async def get_simulation_events(
    simulation_id: UUID,
    user: Annotated[dict, Depends(require_permission("simulation:read"))],
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Get events from simulation."""
    engine = get_simulation_engine()
    simulation = engine.get_simulation(simulation_id)

    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    events = simulation.events_log[offset:offset + limit]

    return {
        "simulation_id": str(simulation_id),
        "total_events": len(simulation.events_log),
        "returned_events": len(events),
        "offset": offset,
        "events": events,
    }


@router.get("/{simulation_id}/agents")
async def get_simulation_agents(
    simulation_id: UUID,
    user: Annotated[dict, Depends(require_permission("simulation:read"))],
    agent_type: AgentType | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    """Get agents from simulation."""
    engine = get_simulation_engine()
    simulation = engine.get_simulation(simulation_id)

    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found",
        )

    agents = simulation.agents

    if agent_type:
        agents = [a for a in agents if a.agent_type == agent_type]

    if state:
        agents = [a for a in agents if a.state == state]

    return {
        "simulation_id": str(simulation_id),
        "total_agents": len(simulation.agents),
        "filtered_agents": len(agents),
        "agents": [
            {
                "agent_id": str(a.agent_id),
                "agent_type": a.agent_type.value,
                "name": a.name,
                "state": a.state,
                "position": {
                    "latitude": a.position.latitude,
                    "longitude": a.position.longitude,
                },
                "velocity": {
                    "speed_kmh": a.velocity[0],
                    "heading_deg": a.velocity[1],
                },
            }
            for a in agents
        ],
    }
