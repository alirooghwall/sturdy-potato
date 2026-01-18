"""Realistic sample data for ISR Platform.

Contains sample entities, events, alerts, and threat intelligence
based on realistic Afghanistan scenarios.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4
import random

from .afghanistan import (
    MAJOR_CITIES,
    BORDER_CROSSINGS,
    PROVINCE_DATA,
    THREAT_GROUPS,
    HUMANITARIAN_DATA,
    get_high_risk_provinces,
)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


def generate_sample_entities(count: int = 50) -> list[dict[str, Any]]:
    """Generate realistic sample entities."""
    entities = []
    
    entity_templates = [
        # Vehicles
        {"type": "VEHICLE", "subtype": "military_convoy", "threat": "LOW"},
        {"type": "VEHICLE", "subtype": "civilian_truck", "threat": "UNKNOWN"},
        {"type": "VEHICLE", "subtype": "suspicious_vehicle", "threat": "MEDIUM"},
        {"type": "VEHICLE", "subtype": "VBIED_suspected", "threat": "HIGH"},
        {"type": "VEHICLE", "subtype": "ambulance", "threat": "LOW"},
        
        # Personnel groups
        {"type": "PERSONNEL_GROUP", "subtype": "armed_group", "threat": "HIGH"},
        {"type": "PERSONNEL_GROUP", "subtype": "civilian_gathering", "threat": "LOW"},
        {"type": "PERSONNEL_GROUP", "subtype": "patrol", "threat": "LOW"},
        {"type": "PERSONNEL_GROUP", "subtype": "refugee_group", "threat": "LOW"},
        
        # Facilities
        {"type": "FACILITY", "subtype": "compound", "threat": "UNKNOWN"},
        {"type": "FACILITY", "subtype": "checkpoint", "threat": "LOW"},
        {"type": "FACILITY", "subtype": "weapons_cache_suspected", "threat": "HIGH"},
        {"type": "FACILITY", "subtype": "training_camp_suspected", "threat": "CRITICAL"},
        {"type": "FACILITY", "subtype": "medical_facility", "threat": "LOW"},
        {"type": "FACILITY", "subtype": "school", "threat": "LOW"},
        
        # Communication
        {"type": "COMMUNICATION", "subtype": "radio_signal", "threat": "UNKNOWN"},
        {"type": "COMMUNICATION", "subtype": "encrypted_comms", "threat": "MEDIUM"},
        
        # Infrastructure
        {"type": "INFRASTRUCTURE", "subtype": "bridge", "threat": "LOW"},
        {"type": "INFRASTRUCTURE", "subtype": "power_station", "threat": "LOW"},
        {"type": "INFRASTRUCTURE", "subtype": "IED_suspected_location", "threat": "CRITICAL"},
    ]
    
    high_risk_provinces = get_high_risk_provinces()
    
    for i in range(count):
        template = random.choice(entity_templates)
        
        # Choose location based on threat level
        if template["threat"] in ["HIGH", "CRITICAL"]:
            province = random.choice(high_risk_provinces)
        else:
            province = random.choice(list(PROVINCE_DATA.keys()))
        
        prov_data = PROVINCE_DATA[province]
        
        # Add some randomness to position within province
        lat_offset = random.uniform(-0.5, 0.5)
        lon_offset = random.uniform(-0.5, 0.5)
        
        entity = {
            "entity_id": str(uuid4()),
            "entity_type": template["type"],
            "name": f"{template['subtype'].replace('_', ' ').title()} #{i+1:04d}",
            "description": f"Detected {template['subtype']} in {province} province",
            "classification": "CONFIDENTIAL" if template["threat"] in ["HIGH", "CRITICAL"] else "UNCLASSIFIED",
            "threat_level": template["threat"],
            "status": "ACTIVE",
            "confidence_score": random.uniform(0.6, 0.95),
            "latitude": prov_data["latitude"] + lat_offset,
            "longitude": prov_data["longitude"] + lon_offset,
            "province": province,
            "first_observed": (utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
            "last_observed": (utcnow() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "attributes": {
                "subtype": template["subtype"],
                "source": random.choice(["SIGINT", "HUMINT", "IMINT", "OSINT"]),
                "reliability": random.choice(["A", "B", "C", "D"]),
            },
        }
        entities.append(entity)
    
    return entities


def generate_sample_events(count: int = 100) -> list[dict[str, Any]]:
    """Generate realistic sample security and humanitarian events."""
    events = []
    
    event_types = [
        # Security events
        {"type": "SECURITY", "subtype": "IED_explosion", "severity": "CRITICAL"},
        {"type": "SECURITY", "subtype": "IED_found", "severity": "HIGH"},
        {"type": "SECURITY", "subtype": "armed_clash", "severity": "HIGH"},
        {"type": "SECURITY", "subtype": "suicide_attack", "severity": "CRITICAL"},
        {"type": "SECURITY", "subtype": "rocket_attack", "severity": "HIGH"},
        {"type": "SECURITY", "subtype": "assassination", "severity": "HIGH"},
        {"type": "SECURITY", "subtype": "kidnapping", "severity": "MEDIUM"},
        {"type": "SECURITY", "subtype": "checkpoint_attack", "severity": "HIGH"},
        {"type": "SECURITY", "subtype": "complex_attack", "severity": "CRITICAL"},
        {"type": "SECURITY", "subtype": "night_raid", "severity": "HIGH"},
        {"type": "SECURITY", "subtype": "intimidation", "severity": "MEDIUM"},
        
        # Border events
        {"type": "BORDER", "subtype": "illegal_crossing", "severity": "MEDIUM"},
        {"type": "BORDER", "subtype": "smuggling_detected", "severity": "MEDIUM"},
        {"type": "BORDER", "subtype": "weapons_seizure", "severity": "HIGH"},
        
        # Humanitarian events
        {"type": "HUMANITARIAN", "subtype": "displacement", "severity": "MEDIUM"},
        {"type": "HUMANITARIAN", "subtype": "food_shortage", "severity": "HIGH"},
        {"type": "HUMANITARIAN", "subtype": "medical_emergency", "severity": "HIGH"},
        {"type": "HUMANITARIAN", "subtype": "refugee_influx", "severity": "MEDIUM"},
        {"type": "HUMANITARIAN", "subtype": "aid_distribution", "severity": "LOW"},
        
        # Infrastructure events
        {"type": "INFRASTRUCTURE", "subtype": "road_closure", "severity": "MEDIUM"},
        {"type": "INFRASTRUCTURE", "subtype": "bridge_damage", "severity": "HIGH"},
        {"type": "INFRASTRUCTURE", "subtype": "power_outage", "severity": "MEDIUM"},
        
        # Natural disaster events
        {"type": "NATURAL_DISASTER", "subtype": "earthquake", "severity": "CRITICAL"},
        {"type": "NATURAL_DISASTER", "subtype": "flood", "severity": "HIGH"},
        {"type": "NATURAL_DISASTER", "subtype": "landslide", "severity": "HIGH"},
        {"type": "NATURAL_DISASTER", "subtype": "drought_impact", "severity": "HIGH"},
    ]
    
    high_risk_provinces = get_high_risk_provinces()
    all_provinces = list(PROVINCE_DATA.keys())
    
    for i in range(count):
        template = random.choice(event_types)
        
        # Security events more likely in high-risk areas
        if template["type"] == "SECURITY":
            province = random.choice(high_risk_provinces) if random.random() > 0.3 else random.choice(all_provinces)
        else:
            province = random.choice(all_provinces)
        
        prov_data = PROVINCE_DATA[province]
        lat_offset = random.uniform(-0.3, 0.3)
        lon_offset = random.uniform(-0.3, 0.3)
        
        occurred_at = utcnow() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        casualties = 0
        affected = 0
        if template["severity"] == "CRITICAL":
            casualties = random.randint(5, 50)
            affected = random.randint(100, 1000)
        elif template["severity"] == "HIGH":
            casualties = random.randint(0, 10)
            affected = random.randint(50, 500)
        elif template["type"] == "HUMANITARIAN":
            affected = random.randint(100, 10000)
        
        # Determine perpetrator for security events
        perpetrator = None
        if template["type"] == "SECURITY":
            perpetrator = random.choice(list(THREAT_GROUPS.keys()))
        
        event = {
            "event_id": str(uuid4()),
            "event_type": template["type"],
            "title": f"{template['subtype'].replace('_', ' ').title()} in {province}",
            "description": f"{template['subtype'].replace('_', ' ')} incident reported in {province} province",
            "severity": template["severity"],
            "classification": "CONFIDENTIAL" if template["type"] == "SECURITY" else "UNCLASSIFIED",
            "verification_status": random.choice(["VERIFIED", "UNVERIFIED", "PENDING"]),
            "latitude": prov_data["latitude"] + lat_offset,
            "longitude": prov_data["longitude"] + lon_offset,
            "location_name": f"{province} Province",
            "region": province,
            "occurred_at": occurred_at.isoformat(),
            "reported_at": (occurred_at + timedelta(hours=random.randint(1, 12))).isoformat(),
            "source_type": random.choice(["SIGINT", "HUMINT", "OSINT", "IMINT", "LOCAL_REPORT"]),
            "source_reliability": random.choice(["A", "B", "C", "D", "E"]),
            "casualties_count": casualties,
            "affected_population": affected,
            "attributes": {
                "subtype": template["subtype"],
                "perpetrator": perpetrator,
                "weapons_used": ["IED", "small_arms", "RPG"][: random.randint(1, 3)] if template["type"] == "SECURITY" else None,
            },
        }
        events.append(event)
    
    return events


def generate_sample_alerts(count: int = 30) -> list[dict[str, Any]]:
    """Generate realistic sample alerts."""
    alerts = []
    
    alert_templates = [
        {"type": "THREAT", "title": "Imminent Attack Warning", "severity": "CRITICAL", "priority": 1},
        {"type": "THREAT", "title": "Increased Insurgent Activity", "severity": "HIGH", "priority": 2},
        {"type": "THREAT", "title": "IED Threat on Main Route", "severity": "CRITICAL", "priority": 1},
        {"type": "THREAT", "title": "Suicide Bomber Alert", "severity": "CRITICAL", "priority": 1},
        {"type": "THREAT", "title": "Kidnapping Threat", "severity": "HIGH", "priority": 2},
        {"type": "INTELLIGENCE", "title": "High-Value Target Movement", "severity": "HIGH", "priority": 2},
        {"type": "INTELLIGENCE", "title": "Weapons Cache Located", "severity": "MEDIUM", "priority": 3},
        {"type": "INTELLIGENCE", "title": "Training Camp Activity", "severity": "HIGH", "priority": 2},
        {"type": "BORDER", "title": "Unusual Border Activity", "severity": "MEDIUM", "priority": 3},
        {"type": "BORDER", "title": "Mass Movement Detected", "severity": "HIGH", "priority": 2},
        {"type": "HUMANITARIAN", "title": "Emergency Medical Need", "severity": "HIGH", "priority": 2},
        {"type": "HUMANITARIAN", "title": "Refugee Crisis Alert", "severity": "HIGH", "priority": 2},
        {"type": "HUMANITARIAN", "title": "Food Security Emergency", "severity": "CRITICAL", "priority": 1},
        {"type": "INFRASTRUCTURE", "title": "Critical Infrastructure Threat", "severity": "HIGH", "priority": 2},
        {"type": "CYBER", "title": "Network Intrusion Detected", "severity": "MEDIUM", "priority": 3},
        {"type": "ANOMALY", "title": "Unusual Communication Pattern", "severity": "MEDIUM", "priority": 3},
        {"type": "ANOMALY", "title": "Abnormal Movement Pattern", "severity": "MEDIUM", "priority": 3},
    ]
    
    high_risk_provinces = get_high_risk_provinces()
    
    for i in range(count):
        template = random.choice(alert_templates)
        
        if template["severity"] in ["CRITICAL", "HIGH"]:
            province = random.choice(high_risk_provinces)
        else:
            province = random.choice(list(PROVINCE_DATA.keys()))
        
        prov_data = PROVINCE_DATA[province]
        lat_offset = random.uniform(-0.2, 0.2)
        lon_offset = random.uniform(-0.2, 0.2)
        
        created_at = utcnow() - timedelta(hours=random.randint(0, 72))
        
        # Determine status
        if random.random() < 0.3:
            status = "RESOLVED"
            resolved_at = created_at + timedelta(hours=random.randint(1, 24))
            acknowledged_at = created_at + timedelta(minutes=random.randint(5, 60))
        elif random.random() < 0.5:
            status = "ACKNOWLEDGED"
            resolved_at = None
            acknowledged_at = created_at + timedelta(minutes=random.randint(5, 60))
        else:
            status = "ACTIVE"
            resolved_at = None
            acknowledged_at = None
        
        alert = {
            "alert_id": str(uuid4()),
            "alert_type": template["type"],
            "title": f"{template['title']} - {province}",
            "description": f"{template['title']} reported in {province} province. Immediate attention required.",
            "severity": template["severity"],
            "priority": template["priority"],
            "status": status,
            "source_system": random.choice(["THREAT_ANALYSIS", "ANOMALY_DETECTION", "INTEL_FUSION", "OSINT_MONITOR"]),
            "latitude": prov_data["latitude"] + lat_offset,
            "longitude": prov_data["longitude"] + lon_offset,
            "region": province,
            "created_at": created_at.isoformat(),
            "acknowledged_at": acknowledged_at.isoformat() if acknowledged_at else None,
            "resolved_at": resolved_at.isoformat() if resolved_at else None,
            "attributes": {
                "confidence": random.uniform(0.7, 0.98),
                "ttl_hours": random.choice([6, 12, 24, 48]),
            },
        }
        alerts.append(alert)
    
    return alerts


def generate_sample_narratives(count: int = 50) -> list[dict[str, Any]]:
    """Generate realistic sample narrative/OSINT data."""
    narratives = []
    
    narrative_templates = [
        # Dari/Pashto local news
        {
            "source_type": "LOCAL_NEWS",
            "language": "DARI",
            "content_template": "گزارش‌ها حاکی از افزایش فعالیت نظامی در {province} است. ساکنان محلی نگران امنیت هستند.",
            "narrative_type": "NEWS",
        },
        {
            "source_type": "LOCAL_NEWS", 
            "language": "PASHTO",
            "content_template": "په {province} کې د امنیتي پیښو راپور. سیمه ییز مسؤلین د حالت څارنه کوي.",
            "narrative_type": "NEWS",
        },
        # Social media
        {
            "source_type": "SOCIAL_MEDIA",
            "language": "ENGLISH",
            "content_template": "BREAKING: Reports of explosion near {location}. Emergency services responding. #Afghanistan",
            "narrative_type": "NEWS",
        },
        {
            "source_type": "SOCIAL_MEDIA",
            "language": "ENGLISH",
            "content_template": "Humanitarian crisis worsening in {province}. Thousands displaced. International community must act now!",
            "narrative_type": "OPINION",
        },
        # Propaganda
        {
            "source_type": "SOCIAL_MEDIA",
            "language": "ENGLISH",
            "content_template": "The heroic fighters achieved great victory against the enemy in {province}! Victory is near!",
            "narrative_type": "PROPAGANDA",
        },
        {
            "source_type": "TELEGRAM",
            "language": "DARI",
            "content_template": "فتح بزرگ در {province}! دشمنان شکست خوردند. این پیروزی متعلق به مردم است!",
            "narrative_type": "PROPAGANDA",
        },
        # Rumors
        {
            "source_type": "SOCIAL_MEDIA",
            "language": "ENGLISH",
            "content_template": "UNCONFIRMED: Sources say major operation planned for {province}. Details unclear.",
            "narrative_type": "RUMOR",
        },
        # Humanitarian reports
        {
            "source_type": "NGO_REPORT",
            "language": "ENGLISH",
            "content_template": "WFP reports food insecurity affecting {number} families in {province}. Emergency response needed.",
            "narrative_type": "NEWS",
        },
        {
            "source_type": "UN_REPORT",
            "language": "ENGLISH",
            "content_template": "UNHCR: Displacement continues in {province}. Estimated {number} people affected this month.",
            "narrative_type": "NEWS",
        },
        # Disinformation
        {
            "source_type": "SOCIAL_MEDIA",
            "language": "ENGLISH",
            "content_template": "SHOCKING: Government secretly negotiating with terrorists! Sources confirm meetings in {province}!",
            "narrative_type": "DISINFORMATION",
        },
    ]
    
    provinces = list(PROVINCE_DATA.keys())
    cities = [c.name for c in MAJOR_CITIES]
    
    for i in range(count):
        template = random.choice(narrative_templates)
        province = random.choice(provinces)
        location = random.choice(cities)
        number = random.randint(1000, 50000)
        
        content = template["content_template"].format(
            province=province,
            location=location,
            number=number,
        )
        
        published_at = utcnow() - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
        )
        
        narrative = {
            "document_id": str(uuid4()),
            "source_id": f"{template['source_type'].lower()}_{random.randint(1000, 9999)}",
            "source_type": template["source_type"],
            "content": content,
            "language": template["language"],
            "published_at": published_at.isoformat(),
            "author_id": f"user_{random.randint(10000, 99999)}",
            "location": province,
            "narrative_type": template["narrative_type"],
            "metadata": {
                "likes": random.randint(0, 5000) if "SOCIAL" in template["source_type"] else 0,
                "shares": random.randint(0, 1000) if "SOCIAL" in template["source_type"] else 0,
                "verified_account": random.random() > 0.7,
            },
        }
        narratives.append(narrative)
    
    return narratives


def generate_threat_intelligence() -> list[dict[str, Any]]:
    """Generate realistic threat intelligence reports."""
    intel_reports = []
    
    for group_name, group_data in THREAT_GROUPS.items():
        for area in group_data["areas_of_operation"][:3]:
            report = {
                "report_id": str(uuid4()),
                "threat_actor": group_name,
                "threat_type": group_data["type"],
                "area_of_operation": area,
                "threat_level": group_data["threat_level"],
                "estimated_strength": group_data["estimated_strength"],
                "known_tactics": group_data["tactics"],
                "recent_activity": random.choice([
                    "Increased recruitment observed",
                    "Movement detected near urban areas", 
                    "Communication intercepts indicate planning",
                    "Weapons procurement activity",
                    "Training camp activity detected",
                ]),
                "assessment_date": utcnow().isoformat(),
                "confidence": random.choice(["HIGH", "MEDIUM", "LOW"]),
                "source_reliability": random.choice(["A", "B", "C"]),
            }
            intel_reports.append(report)
    
    return intel_reports


def generate_border_activity(count: int = 20) -> list[dict[str, Any]]:
    """Generate realistic border crossing activity data."""
    activities = []
    
    for crossing in BORDER_CROSSINGS:
        if crossing.attributes.get("status") == "closed":
            continue
            
        for _ in range(count // len(BORDER_CROSSINGS) + 1):
            timestamp = utcnow() - timedelta(hours=random.randint(0, 72))
            
            activity = {
                "activity_id": str(uuid4()),
                "crossing_name": crossing.name,
                "border_with": crossing.attributes.get("border_with"),
                "latitude": crossing.latitude,
                "longitude": crossing.longitude,
                "timestamp": timestamp.isoformat(),
                "activity_type": random.choice([
                    "vehicle_crossing", "pedestrian_crossing", "commercial_cargo",
                    "suspicious_activity", "denied_entry", "humanitarian_convoy",
                ]),
                "direction": random.choice(["inbound", "outbound"]),
                "vehicle_count": random.randint(1, 50),
                "personnel_count": random.randint(5, 200),
                "anomaly_score": random.uniform(0, 1),
                "notes": None,
            }
            
            if activity["anomaly_score"] > 0.7:
                activity["notes"] = random.choice([
                    "Unusual timing for crossing",
                    "Large group without documentation",
                    "Suspicious cargo inspection required",
                    "Known watchlist individual detected",
                ])
            
            activities.append(activity)
    
    return activities


# Pre-generated sample data (generated once, reusable)
SAMPLE_ENTITIES = generate_sample_entities(50)
SAMPLE_EVENTS = generate_sample_events(100)
SAMPLE_ALERTS = generate_sample_alerts(30)
SAMPLE_NARRATIVES = generate_sample_narratives(50)
THREAT_INTEL_REPORTS = generate_threat_intelligence()
BORDER_ACTIVITIES = generate_border_activity(20)
