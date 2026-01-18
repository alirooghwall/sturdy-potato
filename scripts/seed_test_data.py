"""Seed test data for ISR Platform development and testing."""

import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


async def seed_test_data():
    """Seed database with test data."""
    print("Seeding test data...")
    
    # Sample locations in Afghanistan
    locations = [
        {"name": "Kabul", "lat": 34.5553, "lon": 69.2075},
        {"name": "Kandahar", "lat": 31.6089, "lon": 65.7372},
        {"name": "Herat", "lat": 34.3482, "lon": 62.1997},
        {"name": "Mazar-i-Sharif", "lat": 36.7082, "lon": 67.1107},
        {"name": "Jalalabad", "lat": 34.4268, "lon": 70.4532},
    ]
    
    # Sample entities
    entities = []
    for i in range(10):
        entity = {
            "entity_id": str(uuid4()),
            "entity_type": random.choice(["PERSONNEL", "VEHICLE", "FACILITY", "MILITARY_UNIT"]),
            "display_name": f"Test Entity {i+1}",
            "confidence_score": random.uniform(0.6, 0.95),
            "current_position": random.choice(locations),
            "status": "ACTIVE",
            "created_at": utcnow().isoformat(),
        }
        entities.append(entity)
    
    # Sample events
    events = []
    event_types = ["EXPLOSION", "ATTACK", "PROTEST", "BORDER_CROSSING"]
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    for i in range(20):
        loc = random.choice(locations)
        event = {
            "event_id": str(uuid4()),
            "event_type": random.choice(event_types),
            "severity": random.choice(severities),
            "title": f"Test Event {i+1} - {random.choice(event_types)}",
            "summary": f"This is a test event for development purposes.",
            "location": loc,
            "timestamp": (utcnow() - timedelta(hours=random.randint(1, 168))).isoformat(),
            "region": loc["name"],
        }
        events.append(event)
    
    # Sample alerts
    alerts = []
    for i in range(15):
        loc = random.choice(locations)
        alert = {
            "alert_id": str(uuid4()),
            "severity": random.choice(severities),
            "category": random.choice(["SECURITY", "HUMANITARIAN", "INFRASTRUCTURE"]),
            "title": f"Test Alert {i+1}",
            "description": "Test alert for development",
            "location": loc,
            "status": random.choice(["OPEN", "ACKNOWLEDGED", "RESOLVED"]),
            "created_at": (utcnow() - timedelta(hours=random.randint(1, 48))).isoformat(),
        }
        alerts.append(alert)
    
    print(f"\nTest data generated:")
    print(f"  - {len(entities)} entities")
    print(f"  - {len(events)} events")
    print(f"  - {len(alerts)} alerts")
    print(f"\nTODO: Insert into database")
    print(f"(Database models and insertion logic needs to be implemented)\n")
    
    # SQL examples for manual insertion
    print("Sample SQL for manual testing:")
    print("\n-- Entity example:")
    entity = entities[0]
    print(f"""
INSERT INTO entities (entity_id, entity_type, display_name, confidence_score, current_position, status)
VALUES (
    '{entity['entity_id']}',
    '{entity['entity_type']}',
    '{entity['display_name']}',
    {entity['confidence_score']},
    ST_SetSRID(ST_MakePoint({entity['current_position']['lon']}, {entity['current_position']['lat']}), 4326),
    '{entity['status']}'
);
""")
    
    return True


if __name__ == "__main__":
    asyncio.run(seed_test_data())
