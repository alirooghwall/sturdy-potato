"""Tests for simulation engine."""

import pytest
from uuid import uuid4

from src.services.simulation_engine import (
    AgentType,
    DisasterType,
    GeoCoordinate,
    SimulationAgent,
    SimulationEngine,
    SimulationStatus,
    SimulationType,
)


@pytest.fixture
def engine():
    """Create simulation engine instance."""
    return SimulationEngine()


class TestSimulationEngine:
    """Tests for SimulationEngine."""

    def test_create_simulation(self, engine):
        """Test creating a simulation."""
        simulation = engine.create_simulation(
            name="Test Simulation",
            simulation_type=SimulationType.AGENT_BASED,
            description="A test simulation",
        )

        assert simulation is not None
        assert simulation.name == "Test Simulation"
        assert simulation.simulation_type == SimulationType.AGENT_BASED
        assert simulation.status == SimulationStatus.CREATED

    def test_start_simulation(self, engine):
        """Test starting a simulation."""
        simulation = engine.create_simulation(
            name="Test Sim",
            simulation_type=SimulationType.AGENT_BASED,
        )

        started = engine.start_simulation(simulation.simulation_id)

        assert started.status == SimulationStatus.RUNNING

    def test_pause_simulation(self, engine):
        """Test pausing a simulation."""
        simulation = engine.create_simulation(
            name="Test Sim",
            simulation_type=SimulationType.AGENT_BASED,
        )
        engine.start_simulation(simulation.simulation_id)

        paused = engine.pause_simulation(simulation.simulation_id)

        assert paused.status == SimulationStatus.PAUSED

    def test_step_simulation(self, engine):
        """Test stepping a simulation."""
        simulation = engine.create_simulation(
            name="Test Sim",
            simulation_type=SimulationType.AGENT_BASED,
        )
        engine.start_simulation(simulation.simulation_id)

        # Add some agents
        engine.add_agents(
            simulation.simulation_id,
            AgentType.CIVILIAN,
            count=10,
            base_lat=34.5,
            base_lon=69.1,
        )

        initial_time = simulation.current_time
        stepped = engine.step_simulation(simulation.simulation_id, steps=5)

        assert stepped.current_time > initial_time
        # Steps completed is calculated from time difference, may vary slightly
        assert stepped.metrics.get("steps_completed", 0) >= 4

    def test_add_agents(self, engine):
        """Test adding agents to simulation."""
        simulation = engine.create_simulation(
            name="Test Sim",
            simulation_type=SimulationType.AGENT_BASED,
        )

        agents = engine.add_agents(
            simulation.simulation_id,
            AgentType.MILITARY,
            count=5,
            base_lat=34.5,
            base_lon=69.1,
            spread_km=2.0,
        )

        assert len(agents) == 5
        assert all(a.agent_type == AgentType.MILITARY for a in agents)
        assert len(simulation.agents) == 5

    def test_add_disaster(self, engine):
        """Test adding disaster to simulation."""
        simulation = engine.create_simulation(
            name="Test Sim",
            simulation_type=SimulationType.DISASTER,
        )
        engine.start_simulation(simulation.simulation_id)

        disaster = engine.add_disaster(
            simulation.simulation_id,
            disaster_type=DisasterType.FLOOD,
            epicenter_lat=34.5,
            epicenter_lon=69.1,
            magnitude=7.0,
            radius_km=50.0,
            duration_hours=24.0,
        )

        assert disaster is not None
        assert disaster.disaster_type == DisasterType.FLOOD
        assert disaster.magnitude == 7.0
        assert disaster.population_affected > 0

    def test_cancel_simulation(self, engine):
        """Test cancelling a simulation."""
        simulation = engine.create_simulation(
            name="Test Sim",
            simulation_type=SimulationType.AGENT_BASED,
        )

        cancelled = engine.cancel_simulation(simulation.simulation_id)

        assert cancelled.status == SimulationStatus.CANCELLED

    def test_list_scenarios(self, engine):
        """Test listing available scenarios."""
        scenarios = engine.list_scenarios()

        assert len(scenarios) >= 2  # Default scenarios
        assert any("Tora Bora" in s.name for s in scenarios)
        assert any("Flood" in s.name for s in scenarios)

    def test_create_from_scenario(self, engine):
        """Test creating simulation from scenario."""
        scenarios = engine.list_scenarios()
        scenario = scenarios[0]

        simulation = engine.create_simulation(
            name="Test from Scenario",
            simulation_type=SimulationType.SCENARIO_REPLAY,
            scenario_id=scenario.scenario_id,
        )

        assert simulation.start_time == scenario.start_time
        assert len(simulation.agents) > 0

    def test_simulation_not_found(self, engine):
        """Test error when simulation not found."""
        with pytest.raises(ValueError, match="not found"):
            engine.start_simulation(uuid4())

    def test_cannot_start_completed_simulation(self, engine):
        """Test that completed simulations cannot be started."""
        simulation = engine.create_simulation(
            name="Test Sim",
            simulation_type=SimulationType.AGENT_BASED,
        )
        simulation.status = SimulationStatus.COMPLETED

        with pytest.raises(ValueError, match="Cannot start"):
            engine.start_simulation(simulation.simulation_id)


class TestSimulationAgent:
    """Tests for SimulationAgent."""

    def test_agent_move(self):
        """Test agent movement."""
        agent = SimulationAgent(
            agent_id=uuid4(),
            agent_type=AgentType.CIVILIAN,
            name="Test Agent",
            position=GeoCoordinate(latitude=34.5, longitude=69.1),
            velocity=(10.0, 90.0),  # 10 km/h heading east
        )

        initial_lon = agent.position.longitude
        agent.move(1.0)  # Move for 1 hour

        assert agent.position.longitude > initial_lon

    def test_agent_no_move_zero_velocity(self):
        """Test agent doesn't move with zero velocity."""
        agent = SimulationAgent(
            agent_id=uuid4(),
            agent_type=AgentType.CIVILIAN,
            name="Test Agent",
            position=GeoCoordinate(latitude=34.5, longitude=69.1),
            velocity=(0.0, 0.0),
        )

        initial_lat = agent.position.latitude
        initial_lon = agent.position.longitude
        agent.move(1.0)

        assert agent.position.latitude == initial_lat
        assert agent.position.longitude == initial_lon
