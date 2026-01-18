"""Realistic simulation scenarios for Afghanistan.

Contains historical battle recreations, disaster scenarios,
humanitarian crises, and what-if analysis templates.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from .afghanistan import (
    PROVINCE_DATA,
    MAJOR_CITIES,
    BORDER_CROSSINGS,
    STRATEGIC_LOCATIONS,
    THREAT_GROUPS,
    HISTORICAL_SCENARIOS,
    DISASTER_HISTORY,
)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


@dataclass
class ScenarioDefinition:
    """Complete scenario definition for simulation."""
    scenario_id: str
    name: str
    description: str
    category: str  # HISTORICAL, DISASTER, HUMANITARIAN, WHAT_IF, TRAINING
    region: str
    start_time: datetime
    end_time: datetime
    time_step_minutes: int = 15
    
    # Initial setup
    initial_agents: list[dict[str, Any]] = field(default_factory=list)
    initial_events: list[dict[str, Any]] = field(default_factory=list)
    triggers: list[dict[str, Any]] = field(default_factory=list)
    
    # Parameters
    parameters: dict[str, Any] = field(default_factory=dict)
    objectives: list[str] = field(default_factory=list)
    
    # Metadata
    difficulty: str = "MEDIUM"  # EASY, MEDIUM, HARD, EXPERT
    estimated_duration_hours: float = 2.0
    tags: list[str] = field(default_factory=list)


# Historical Battle Scenarios
TORA_BORA_SCENARIO = ScenarioDefinition(
    scenario_id="hist_tora_bora_2001",
    name="Battle of Tora Bora (December 2001)",
    description="""
    Recreation of the December 2001 battle in the White Mountains of Nangarhar Province.
    Coalition and Afghan forces assault al-Qaeda positions in the cave complex.
    Objective: Clear enemy positions and prevent escape to Pakistan border.
    """,
    category="HISTORICAL",
    region="Nangarhar",
    start_time=datetime(2001, 12, 12, 6, 0, tzinfo=UTC),
    end_time=datetime(2001, 12, 17, 18, 0, tzinfo=UTC),
    time_step_minutes=30,
    initial_agents=[
        # Coalition/Afghan forces
        {"agent_type": "MILITARY", "count": 100, "faction": "coalition",
         "position": {"lat": 34.15, "lon": 70.10}, "attributes": {"unit": "Special Forces"}},
        {"agent_type": "MILITARY", "count": 1500, "faction": "afghan_allies",
         "position": {"lat": 34.12, "lon": 70.12}, "attributes": {"unit": "Eastern Alliance"}},
        # Enemy forces
        {"agent_type": "INSURGENT", "count": 1000, "faction": "al_qaeda",
         "position": {"lat": 34.08, "lon": 70.15}, "attributes": {"fortified": True}},
        {"agent_type": "INSURGENT", "count": 500, "faction": "al_qaeda",
         "position": {"lat": 34.05, "lon": 70.18}, "attributes": {"reserve": True}},
        # Civilians (refugees fleeing)
        {"agent_type": "CIVILIAN", "count": 200, "faction": "neutral",
         "position": {"lat": 34.10, "lon": 70.05}, "attributes": {"refugees": True}},
    ],
    triggers=[
        {"time_offset_hours": 0, "event": "air_strike_begins", "target": "cave_complex"},
        {"time_offset_hours": 12, "event": "ground_assault_phase1"},
        {"time_offset_hours": 36, "event": "enemy_breakout_attempt"},
        {"time_offset_hours": 72, "event": "border_escape_window"},
    ],
    parameters={
        "terrain": "mountainous",
        "elevation_range": [2000, 4000],
        "weather": "cold_clear",
        "visibility": "good",
        "air_support": True,
        "border_distance_km": 15,
    },
    objectives=[
        "Neutralize enemy leadership positions",
        "Prevent escape to Pakistan border",
        "Minimize civilian casualties",
        "Capture intelligence materials",
    ],
    difficulty="HARD",
    estimated_duration_hours=4.0,
    tags=["historical", "mountain_warfare", "counterterrorism", "2001"],
)

KUNDUZ_2015_SCENARIO = ScenarioDefinition(
    scenario_id="hist_kunduz_2015",
    name="Fall of Kunduz (September 2015)",
    description="""
    Recreation of the September 2015 Taliban assault on Kunduz city.
    First provincial capital to fall since 2001. Analyzes urban defense challenges.
    """,
    category="HISTORICAL",
    region="Kunduz",
    start_time=datetime(2015, 9, 28, 2, 0, tzinfo=UTC),
    end_time=datetime(2015, 10, 13, 18, 0, tzinfo=UTC),
    time_step_minutes=60,
    initial_agents=[
        # Afghan Security Forces
        {"agent_type": "MILITARY", "count": 2000, "faction": "ansf",
         "position": {"lat": 36.73, "lon": 68.86}, "attributes": {"unit": "ANA"}},
        {"agent_type": "POLICE", "count": 1500, "faction": "ansf",
         "position": {"lat": 36.72, "lon": 68.87}, "attributes": {"unit": "ANP"}},
        # Taliban forces
        {"agent_type": "INSURGENT", "count": 500, "faction": "taliban",
         "position": {"lat": 36.78, "lon": 68.80}, "attributes": {"assault_group": 1}},
        {"agent_type": "INSURGENT", "count": 300, "faction": "taliban",
         "position": {"lat": 36.68, "lon": 68.90}, "attributes": {"assault_group": 2}},
        {"agent_type": "INSURGENT", "count": 200, "faction": "taliban",
         "position": {"lat": 36.75, "lon": 68.92}, "attributes": {"assault_group": 3}},
        # Civilian population
        {"agent_type": "CIVILIAN", "count": 5000, "faction": "neutral",
         "position": {"lat": 36.73, "lon": 68.86}, "attributes": {"urban": True}},
    ],
    triggers=[
        {"time_offset_hours": 0, "event": "multi_axis_assault"},
        {"time_offset_hours": 6, "event": "government_compound_surrounded"},
        {"time_offset_hours": 12, "event": "prison_break"},
        {"time_offset_hours": 24, "event": "city_center_falls"},
        {"time_offset_hours": 168, "event": "counteroffensive_begins"},
    ],
    parameters={
        "terrain": "urban",
        "population_density": "high",
        "weather": "clear",
        "air_support_available": True,
        "reinforcement_possible": True,
    },
    objectives=[
        "Defend key government buildings",
        "Protect civilian population",
        "Maintain communication with reinforcements",
        "Retake city if fallen",
    ],
    difficulty="EXPERT",
    estimated_duration_hours=6.0,
    tags=["historical", "urban_warfare", "defense", "2015"],
)

# Disaster Scenarios
HERAT_EARTHQUAKE_SCENARIO = ScenarioDefinition(
    scenario_id="disaster_herat_earthquake",
    name="Herat Earthquake Response (2023 Type)",
    description="""
    Simulation of earthquake response based on October 2023 Herat earthquakes.
    Multiple 6.3 magnitude events causing widespread destruction.
    Focus on search and rescue, medical response, and shelter operations.
    """,
    category="DISASTER",
    region="Herat",
    start_time=utcnow(),
    end_time=utcnow() + timedelta(days=7),
    time_step_minutes=30,
    initial_agents=[
        # First responders
        {"agent_type": "HUMANITARIAN", "count": 50, "faction": "local_responders",
         "position": {"lat": 34.35, "lon": 62.20}, "attributes": {"type": "search_rescue"}},
        {"agent_type": "HUMANITARIAN", "count": 30, "faction": "medical",
         "position": {"lat": 34.36, "lon": 62.21}, "attributes": {"type": "medical_team"}},
        # International aid
        {"agent_type": "HUMANITARIAN", "count": 100, "faction": "un_agencies",
         "position": {"lat": 34.21, "lon": 62.23}, "attributes": {"type": "aid_workers", "delayed_hours": 24}},
        # Affected population
        {"agent_type": "CIVILIAN", "count": 10000, "faction": "affected",
         "position": {"lat": 34.35, "lon": 62.20}, "attributes": {"injured_pct": 15, "displaced": True}},
    ],
    initial_events=[
        {"time": 0, "type": "earthquake", "magnitude": 6.3, "epicenter": {"lat": 34.35, "lon": 62.00}, "depth_km": 10},
        {"time": 4, "type": "aftershock", "magnitude": 5.5},
        {"time": 24, "type": "aftershock", "magnitude": 6.3},
    ],
    parameters={
        "earthquake_magnitude": 6.3,
        "affected_radius_km": 50,
        "building_collapse_rate": 0.4,
        "hospital_capacity": 500,
        "shelter_capacity": 5000,
        "road_damage_pct": 30,
    },
    objectives=[
        "Maximize search and rescue within 72-hour window",
        "Establish field hospitals",
        "Set up emergency shelters",
        "Coordinate international aid arrival",
        "Prevent secondary casualties",
    ],
    difficulty="HARD",
    estimated_duration_hours=4.0,
    tags=["disaster", "earthquake", "humanitarian", "search_rescue"],
)

KABUL_FLOOD_SCENARIO = ScenarioDefinition(
    scenario_id="disaster_kabul_flood",
    name="Kabul River Flash Flood",
    description="""
    Flash flood scenario in Kabul River basin following heavy rainfall.
    Simulates rapid onset flooding affecting urban and peri-urban areas.
    """,
    category="DISASTER",
    region="Kabul",
    start_time=utcnow(),
    end_time=utcnow() + timedelta(days=3),
    time_step_minutes=15,
    initial_agents=[
        # Emergency services
        {"agent_type": "HUMANITARIAN", "count": 100, "faction": "emergency_services",
         "position": {"lat": 34.55, "lon": 69.21}},
        # Affected population in flood zone
        {"agent_type": "CIVILIAN", "count": 20000, "faction": "at_risk",
         "position": {"lat": 34.52, "lon": 69.18}, "attributes": {"flood_zone": True}},
        {"agent_type": "CIVILIAN", "count": 50000, "faction": "safe_zone",
         "position": {"lat": 34.58, "lon": 69.22}},
    ],
    triggers=[
        {"time_offset_hours": 0, "event": "heavy_rainfall_begins"},
        {"time_offset_hours": 6, "event": "flood_warning_issued"},
        {"time_offset_hours": 12, "event": "river_overflow_begins"},
        {"time_offset_hours": 18, "event": "flood_peak"},
        {"time_offset_hours": 36, "event": "waters_receding"},
    ],
    parameters={
        "rainfall_mm": 150,
        "river_level_rise_m": 4.0,
        "flood_extent_km2": 25,
        "evacuation_routes": 5,
        "shelter_locations": 8,
    },
    objectives=[
        "Issue early warnings to at-risk population",
        "Evacuate flood zones before peak",
        "Establish emergency shelters",
        "Conduct water rescues",
        "Restore critical infrastructure",
    ],
    difficulty="MEDIUM",
    estimated_duration_hours=3.0,
    tags=["disaster", "flood", "urban", "evacuation"],
)

# Humanitarian Crisis Scenarios
REFUGEE_CRISIS_SCENARIO = ScenarioDefinition(
    scenario_id="humanitarian_refugee_influx",
    name="Mass Displacement Crisis",
    description="""
    Large-scale internal displacement scenario due to conflict escalation.
    Multiple provinces affected with movement toward major cities and borders.
    """,
    category="HUMANITARIAN",
    region="Multiple",
    start_time=utcnow(),
    end_time=utcnow() + timedelta(days=14),
    time_step_minutes=60,
    initial_agents=[
        # Displaced populations from conflict zones
        {"agent_type": "CIVILIAN", "count": 50000, "faction": "idp",
         "position": {"lat": 31.63, "lon": 65.74}, "attributes": {"origin": "Kandahar", "destination": "Kabul"}},
        {"agent_type": "CIVILIAN", "count": 30000, "faction": "idp",
         "position": {"lat": 31.58, "lon": 64.36}, "attributes": {"origin": "Helmand", "destination": "Herat"}},
        {"agent_type": "CIVILIAN", "count": 20000, "faction": "idp",
         "position": {"lat": 36.73, "lon": 68.86}, "attributes": {"origin": "Kunduz", "destination": "Kabul"}},
        # Humanitarian workers
        {"agent_type": "HUMANITARIAN", "count": 200, "faction": "unhcr",
         "position": {"lat": 34.55, "lon": 69.21}},
        {"agent_type": "HUMANITARIAN", "count": 150, "faction": "wfp",
         "position": {"lat": 34.55, "lon": 69.21}},
    ],
    parameters={
        "total_displaced": 100000,
        "daily_movement_km": 30,
        "food_requirement_tons_day": 150,
        "water_requirement_liters_day": 2000000,
        "medical_cases_pct": 5,
        "camp_capacity": 50000,
    },
    objectives=[
        "Track and monitor displacement flows",
        "Establish reception centers",
        "Provide emergency food and water",
        "Set up medical facilities",
        "Coordinate with border authorities",
    ],
    difficulty="HARD",
    estimated_duration_hours=5.0,
    tags=["humanitarian", "displacement", "refugee", "logistics"],
)

DROUGHT_RESPONSE_SCENARIO = ScenarioDefinition(
    scenario_id="humanitarian_drought",
    name="Northern Afghanistan Drought Response",
    description="""
    Extended drought scenario affecting northern provinces.
    Focus on food security, water access, and livestock survival.
    """,
    category="HUMANITARIAN",
    region="Balkh/Jowzjan/Faryab",
    start_time=utcnow(),
    end_time=utcnow() + timedelta(days=90),
    time_step_minutes=360,  # 6-hour steps for long-term scenario
    initial_agents=[
        # Affected farming communities
        {"agent_type": "CIVILIAN", "count": 100000, "faction": "farmers",
         "position": {"lat": 36.71, "lon": 67.11}, "attributes": {"livelihood": "agriculture"}},
        {"agent_type": "CIVILIAN", "count": 50000, "faction": "herders",
         "position": {"lat": 36.67, "lon": 65.75}, "attributes": {"livelihood": "livestock"}},
        # Aid organizations
        {"agent_type": "HUMANITARIAN", "count": 100, "faction": "fao",
         "position": {"lat": 36.71, "lon": 67.11}},
        {"agent_type": "HUMANITARIAN", "count": 80, "faction": "wfp",
         "position": {"lat": 36.71, "lon": 67.11}},
    ],
    parameters={
        "rainfall_deficit_pct": 60,
        "crop_failure_pct": 70,
        "livestock_mortality_pct": 30,
        "water_sources_dried": 40,
        "food_insecure_population": 3000000,
    },
    objectives=[
        "Assess drought impact across region",
        "Distribute emergency food assistance",
        "Provide livestock feed and veterinary care",
        "Establish water trucking operations",
        "Plan medium-term recovery",
    ],
    difficulty="HARD",
    estimated_duration_hours=6.0,
    tags=["humanitarian", "drought", "food_security", "agriculture"],
)

# What-If Analysis Scenarios
BORDER_SURGE_SCENARIO = ScenarioDefinition(
    scenario_id="whatif_border_surge",
    name="Border Crossing Surge Analysis",
    description="""
    What-if scenario analyzing impact of sudden surge in border crossings.
    Tests border security response and humanitarian capacity.
    """,
    category="WHAT_IF",
    region="Nangarhar/Kandahar",
    start_time=utcnow(),
    end_time=utcnow() + timedelta(days=7),
    time_step_minutes=60,
    initial_agents=[
        # Border security
        {"agent_type": "BORDER_PATROL", "count": 200, "faction": "border_force",
         "position": {"lat": 34.11, "lon": 71.09}},
        {"agent_type": "BORDER_PATROL", "count": 150, "faction": "border_force",
         "position": {"lat": 30.99, "lon": 66.40}},
        # Normal crossing traffic
        {"agent_type": "CIVILIAN", "count": 5000, "faction": "travelers",
         "position": {"lat": 34.11, "lon": 71.09}},
        # Surge population
        {"agent_type": "CIVILIAN", "count": 50000, "faction": "surge",
         "position": {"lat": 34.00, "lon": 71.20}, "attributes": {"delayed_hours": 12}},
    ],
    triggers=[
        {"time_offset_hours": 12, "event": "surge_begins"},
        {"time_offset_hours": 24, "event": "border_congestion_critical"},
        {"time_offset_hours": 36, "event": "humanitarian_response_activated"},
    ],
    parameters={
        "normal_daily_crossings": 5000,
        "surge_multiplier": 10,
        "processing_capacity_per_hour": 500,
        "humanitarian_staging_capacity": 10000,
    },
    objectives=[
        "Model border processing capacity",
        "Identify bottlenecks",
        "Test humanitarian response triggers",
        "Analyze security vulnerabilities",
    ],
    difficulty="MEDIUM",
    estimated_duration_hours=3.0,
    tags=["what_if", "border", "capacity_planning", "security"],
)

MULTI_AXIS_ATTACK_SCENARIO = ScenarioDefinition(
    scenario_id="whatif_multi_axis",
    name="Multi-Province Coordinated Attack",
    description="""
    What-if analysis of coordinated insurgent attacks across multiple provinces.
    Tests response coordination and resource allocation.
    """,
    category="WHAT_IF",
    region="Multiple",
    start_time=utcnow(),
    end_time=utcnow() + timedelta(days=3),
    time_step_minutes=30,
    initial_agents=[
        # Security forces distributed across provinces
        {"agent_type": "MILITARY", "count": 500, "faction": "ansf",
         "position": {"lat": 34.55, "lon": 69.21}, "attributes": {"province": "Kabul"}},
        {"agent_type": "MILITARY", "count": 400, "faction": "ansf",
         "position": {"lat": 31.63, "lon": 65.74}, "attributes": {"province": "Kandahar"}},
        {"agent_type": "MILITARY", "count": 300, "faction": "ansf",
         "position": {"lat": 36.73, "lon": 68.86}, "attributes": {"province": "Kunduz"}},
        # Insurgent cells
        {"agent_type": "INSURGENT", "count": 200, "faction": "insurgent",
         "position": {"lat": 34.50, "lon": 69.15}, "attributes": {"target": "Kabul"}},
        {"agent_type": "INSURGENT", "count": 150, "faction": "insurgent",
         "position": {"lat": 31.58, "lon": 65.68}, "attributes": {"target": "Kandahar"}},
        {"agent_type": "INSURGENT", "count": 100, "faction": "insurgent",
         "position": {"lat": 36.68, "lon": 68.80}, "attributes": {"target": "Kunduz"}},
    ],
    triggers=[
        {"time_offset_hours": 0, "event": "simultaneous_attacks_begin"},
        {"time_offset_hours": 1, "event": "secondary_attacks"},
        {"time_offset_hours": 6, "event": "reinforcement_decision"},
    ],
    parameters={
        "attack_provinces": ["Kabul", "Kandahar", "Kunduz"],
        "coordination_level": "HIGH",
        "available_reserves": 1000,
        "air_support_sorties": 20,
    },
    objectives=[
        "Model simultaneous attack response",
        "Test resource allocation decisions",
        "Analyze communication requirements",
        "Identify capability gaps",
    ],
    difficulty="EXPERT",
    estimated_duration_hours=4.0,
    tags=["what_if", "security", "coordination", "multi_domain"],
)

# Training Scenarios
CHECKPOINT_OPERATIONS_SCENARIO = ScenarioDefinition(
    scenario_id="training_checkpoint",
    name="Checkpoint Operations Training",
    description="""
    Training scenario for checkpoint operations and threat identification.
    Includes normal traffic, suspicious vehicles, and VBIED threats.
    """,
    category="TRAINING",
    region="Kabul",
    start_time=utcnow(),
    end_time=utcnow() + timedelta(hours=8),
    time_step_minutes=5,
    initial_agents=[
        # Checkpoint personnel
        {"agent_type": "POLICE", "count": 20, "faction": "checkpoint",
         "position": {"lat": 34.52, "lon": 69.17}},
        # Normal traffic
        {"agent_type": "CIVILIAN", "count": 200, "faction": "traffic",
         "position": {"lat": 34.50, "lon": 69.15}, "attributes": {"vehicle": True}},
    ],
    triggers=[
        {"time_offset_hours": 1, "event": "suspicious_vehicle_approaches"},
        {"time_offset_hours": 3, "event": "vip_convoy_scheduled"},
        {"time_offset_hours": 5, "event": "vbied_attempt"},
    ],
    parameters={
        "traffic_volume_per_hour": 100,
        "suspicious_vehicle_rate": 0.02,
        "threat_rate": 0.005,
    },
    objectives=[
        "Practice threat identification",
        "Test response procedures",
        "Minimize false positives",
        "Ensure civilian safety",
    ],
    difficulty="EASY",
    estimated_duration_hours=2.0,
    tags=["training", "checkpoint", "security", "threat_id"],
)


# Collect all scenarios
ALL_SCENARIOS: dict[str, ScenarioDefinition] = {
    # Historical
    "hist_tora_bora_2001": TORA_BORA_SCENARIO,
    "hist_kunduz_2015": KUNDUZ_2015_SCENARIO,
    
    # Disasters
    "disaster_herat_earthquake": HERAT_EARTHQUAKE_SCENARIO,
    "disaster_kabul_flood": KABUL_FLOOD_SCENARIO,
    
    # Humanitarian
    "humanitarian_refugee_influx": REFUGEE_CRISIS_SCENARIO,
    "humanitarian_drought": DROUGHT_RESPONSE_SCENARIO,
    
    # What-If
    "whatif_border_surge": BORDER_SURGE_SCENARIO,
    "whatif_multi_axis": MULTI_AXIS_ATTACK_SCENARIO,
    
    # Training
    "training_checkpoint": CHECKPOINT_OPERATIONS_SCENARIO,
}


def get_scenario(scenario_id: str) -> ScenarioDefinition | None:
    """Get a scenario by ID."""
    return ALL_SCENARIOS.get(scenario_id)


def list_scenarios_by_category(category: str | None = None) -> list[ScenarioDefinition]:
    """List scenarios, optionally filtered by category."""
    scenarios = list(ALL_SCENARIOS.values())
    if category:
        scenarios = [s for s in scenarios if s.category == category]
    return scenarios


def get_scenario_summary() -> dict[str, Any]:
    """Get summary of all available scenarios."""
    categories = {}
    for scenario in ALL_SCENARIOS.values():
        if scenario.category not in categories:
            categories[scenario.category] = []
        categories[scenario.category].append({
            "id": scenario.scenario_id,
            "name": scenario.name,
            "region": scenario.region,
            "difficulty": scenario.difficulty,
            "duration_hours": scenario.estimated_duration_hours,
        })
    
    return {
        "total_scenarios": len(ALL_SCENARIOS),
        "categories": categories,
    }
