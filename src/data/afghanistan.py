"""Realistic Afghanistan geographic and demographic data.

Contains actual provinces, districts, cities, border crossings,
and demographic information for simulation and analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Province(str, Enum):
    """Afghanistan's 34 provinces."""
    KABUL = "Kabul"
    KANDAHAR = "Kandahar"
    HERAT = "Herat"
    BALKH = "Balkh"
    NANGARHAR = "Nangarhar"
    KUNDUZ = "Kunduz"
    BAGHLAN = "Baghlan"
    GHAZNI = "Ghazni"
    HELMAND = "Helmand"
    FARYAB = "Faryab"
    BADAKHSHAN = "Badakhshan"
    TAKHAR = "Takhar"
    JOWZJAN = "Jowzjan"
    PAKTIA = "Paktia"
    PARWAN = "Parwan"
    LAGHMAN = "Laghman"
    SAMANGAN = "Samangan"
    WARDAK = "Wardak"
    KUNAR = "Kunar"
    KAPISA = "Kapisa"
    BAMYAN = "Bamyan"
    PAKTIKA = "Paktika"
    BADGHIS = "Badghis"
    LOGAR = "Logar"
    KHOST = "Khost"
    DAYKUNDI = "Daykundi"
    URUZGAN = "Uruzgan"
    ZABUL = "Zabul"
    NIMROZ = "Nimroz"
    FARAH = "Farah"
    GHOR = "Ghor"
    SAR_E_PUL = "Sar-e Pul"
    NURISTAN = "Nuristan"
    PANJSHIR = "Panjshir"


@dataclass
class GeoLocation:
    """Geographic location with coordinates."""
    name: str
    latitude: float
    longitude: float
    province: str
    population: int = 0
    elevation_m: int = 0
    location_type: str = "city"  # city, town, village, base, crossing
    attributes: dict[str, Any] = field(default_factory=dict)


# Major cities and their coordinates
MAJOR_CITIES: list[GeoLocation] = [
    GeoLocation("Kabul", 34.5553, 69.2075, "Kabul", 4_600_000, 1791, "capital"),
    GeoLocation("Kandahar", 31.6289, 65.7372, "Kandahar", 614_000, 1010, "city"),
    GeoLocation("Herat", 34.3529, 62.2040, "Herat", 574_000, 920, "city"),
    GeoLocation("Mazar-i-Sharif", 36.7069, 67.1147, "Balkh", 469_000, 357, "city"),
    GeoLocation("Jalalabad", 34.4253, 70.4536, "Nangarhar", 356_000, 575, "city"),
    GeoLocation("Kunduz", 36.7286, 68.8578, "Kunduz", 304_000, 407, "city"),
    GeoLocation("Ghazni", 33.5536, 68.4269, "Ghazni", 270_000, 2219, "city"),
    GeoLocation("Lashkar Gah", 31.5830, 64.3639, "Helmand", 201_000, 773, "city"),
    GeoLocation("Taloqan", 36.7361, 69.5347, "Takhar", 196_000, 800, "city"),
    GeoLocation("Pul-e-Khumri", 35.9500, 68.7167, "Baghlan", 174_000, 650, "city"),
    GeoLocation("Khost", 33.3386, 69.9203, "Khost", 153_000, 1167, "city"),
    GeoLocation("Sheberghan", 36.6675, 65.7536, "Jowzjan", 148_000, 360, "city"),
    GeoLocation("Charikar", 35.0167, 69.1667, "Parwan", 130_000, 1600, "city"),
    GeoLocation("Farah", 32.3747, 62.1147, "Farah", 75_000, 660, "city"),
    GeoLocation("Fayzabad", 37.1167, 70.5833, "Badakhshan", 71_000, 1200, "city"),
    GeoLocation("Zaranj", 30.9603, 61.8606, "Nimroz", 49_000, 483, "city"),
    GeoLocation("Gardez", 33.6000, 69.2167, "Paktia", 103_000, 2300, "city"),
    GeoLocation("Mahmud-i-Raqi", 35.0167, 69.3333, "Kapisa", 60_000, 1800, "city"),
    GeoLocation("Asadabad", 34.8667, 71.1500, "Kunar", 48_000, 935, "city"),
    GeoLocation("Bamyan", 34.8167, 67.8167, "Bamyan", 61_000, 2550, "city"),
]

# Border crossings with neighboring countries
BORDER_CROSSINGS: list[GeoLocation] = [
    # Pakistan border (Durand Line - 2,670 km)
    GeoLocation("Torkham", 34.1058, 71.0931, "Nangarhar", 0, 550, "crossing",
                {"border_with": "Pakistan", "traffic": "high", "status": "active"}),
    GeoLocation("Spin Boldak", 30.9939, 66.3978, "Kandahar", 0, 1050, "crossing",
                {"border_with": "Pakistan", "traffic": "high", "status": "active"}),
    GeoLocation("Ghulam Khan", 33.2167, 69.7833, "Khost", 0, 1100, "crossing",
                {"border_with": "Pakistan", "traffic": "medium", "status": "active"}),
    GeoLocation("Angoor Ada", 32.6833, 69.7833, "Paktika", 0, 1400, "crossing",
                {"border_with": "Pakistan", "traffic": "low", "status": "restricted"}),
    
    # Iran border (936 km)
    GeoLocation("Islam Qala", 34.6667, 61.0667, "Herat", 0, 920, "crossing",
                {"border_with": "Iran", "traffic": "high", "status": "active"}),
    GeoLocation("Zaranj-Milak", 30.9667, 61.8667, "Nimroz", 0, 480, "crossing",
                {"border_with": "Iran", "traffic": "medium", "status": "active"}),
    
    # Turkmenistan border (804 km)
    GeoLocation("Torghundi", 35.2667, 62.3667, "Herat", 0, 400, "crossing",
                {"border_with": "Turkmenistan", "traffic": "low", "status": "active"}),
    GeoLocation("Aqina", 36.9167, 65.5833, "Faryab", 0, 300, "crossing",
                {"border_with": "Turkmenistan", "traffic": "low", "status": "active"}),
    
    # Uzbekistan border (144 km)
    GeoLocation("Hairatan", 37.2333, 67.0833, "Balkh", 0, 282, "crossing",
                {"border_with": "Uzbekistan", "traffic": "high", "status": "active"}),
    
    # Tajikistan border (1,357 km)
    GeoLocation("Shir Khan Bandar", 37.0500, 68.8167, "Kunduz", 0, 350, "crossing",
                {"border_with": "Tajikistan", "traffic": "medium", "status": "active"}),
    GeoLocation("Ishkashim", 36.7167, 71.6167, "Badakhshan", 0, 2500, "crossing",
                {"border_with": "Tajikistan", "traffic": "low", "status": "active"}),
    
    # China border (76 km - Wakhan Corridor)
    GeoLocation("Wakhan Corridor", 37.0500, 73.5000, "Badakhshan", 0, 4800, "crossing",
                {"border_with": "China", "traffic": "none", "status": "closed"}),
]

# Strategic locations and infrastructure
STRATEGIC_LOCATIONS: list[GeoLocation] = [
    # Airports
    GeoLocation("Hamid Karzai International Airport", 34.5658, 69.2125, "Kabul", 0, 1792, "airport",
                {"icao": "OAKB", "type": "international", "runways": 2}),
    GeoLocation("Kandahar International Airport", 31.5058, 65.8478, "Kandahar", 0, 1015, "airport",
                {"icao": "OAKN", "type": "international", "runways": 1}),
    GeoLocation("Herat International Airport", 34.2100, 62.2283, "Herat", 0, 977, "airport",
                {"icao": "OAHR", "type": "international", "runways": 1}),
    GeoLocation("Mazar-i-Sharif International Airport", 36.7069, 67.2097, "Balkh", 0, 378, "airport",
                {"icao": "OAMS", "type": "international", "runways": 1}),
    GeoLocation("Bagram Airfield", 34.9461, 69.2650, "Parwan", 0, 1492, "airfield",
                {"icao": "OAIX", "type": "military", "runways": 2}),
    
    # Key mountain passes
    GeoLocation("Salang Pass", 35.3167, 69.0333, "Parwan", 0, 3878, "pass",
                {"route": "Kabul-Mazar", "strategic": True}),
    GeoLocation("Khyber Pass", 34.1000, 71.0833, "Nangarhar", 0, 1070, "pass",
                {"route": "Kabul-Peshawar", "strategic": True}),
    
    # Historic sites
    GeoLocation("Tora Bora", 34.0833, 70.1500, "Nangarhar", 0, 4000, "mountain",
                {"historic": True, "terrain": "caves"}),
    GeoLocation("Panjshir Valley", 35.3000, 70.0000, "Panjshir", 0, 2200, "valley",
                {"historic": True, "terrain": "valley"}),
]

# Province data with demographics and risk levels
PROVINCE_DATA: dict[str, dict[str, Any]] = {
    "Kabul": {
        "capital": "Kabul",
        "population": 4_600_000,
        "area_km2": 4_462,
        "districts": 15,
        "latitude": 34.5553,
        "longitude": 69.2075,
        "security_level": "medium",
        "humanitarian_need": "high",
        "border_province": False,
        "ethnic_majority": "Tajik/Pashtun",
    },
    "Kandahar": {
        "capital": "Kandahar",
        "population": 1_300_000,
        "area_km2": 54_022,
        "districts": 18,
        "latitude": 31.6289,
        "longitude": 65.7372,
        "security_level": "critical",
        "humanitarian_need": "high",
        "border_province": True,
        "ethnic_majority": "Pashtun",
    },
    "Herat": {
        "capital": "Herat",
        "population": 2_000_000,
        "area_km2": 54_778,
        "districts": 16,
        "latitude": 34.3529,
        "longitude": 62.2040,
        "security_level": "medium",
        "humanitarian_need": "medium",
        "border_province": True,
        "ethnic_majority": "Tajik/Pashtun",
    },
    "Balkh": {
        "capital": "Mazar-i-Sharif",
        "population": 1_500_000,
        "area_km2": 17_249,
        "districts": 15,
        "latitude": 36.7069,
        "longitude": 67.1147,
        "security_level": "low",
        "humanitarian_need": "medium",
        "border_province": True,
        "ethnic_majority": "Uzbek/Tajik",
    },
    "Nangarhar": {
        "capital": "Jalalabad",
        "population": 1_600_000,
        "area_km2": 7_727,
        "districts": 22,
        "latitude": 34.4253,
        "longitude": 70.4536,
        "security_level": "high",
        "humanitarian_need": "high",
        "border_province": True,
        "ethnic_majority": "Pashtun",
    },
    "Helmand": {
        "capital": "Lashkar Gah",
        "population": 900_000,
        "area_km2": 58_584,
        "districts": 14,
        "latitude": 31.5830,
        "longitude": 64.3639,
        "security_level": "critical",
        "humanitarian_need": "critical",
        "border_province": True,
        "ethnic_majority": "Pashtun",
    },
    "Kunduz": {
        "capital": "Kunduz",
        "population": 1_000_000,
        "area_km2": 8_040,
        "districts": 7,
        "latitude": 36.7286,
        "longitude": 68.8578,
        "security_level": "high",
        "humanitarian_need": "high",
        "border_province": True,
        "ethnic_majority": "Pashtun/Uzbek",
    },
    "Ghazni": {
        "capital": "Ghazni",
        "population": 1_300_000,
        "area_km2": 22_915,
        "districts": 19,
        "latitude": 33.5536,
        "longitude": 68.4269,
        "security_level": "high",
        "humanitarian_need": "high",
        "border_province": False,
        "ethnic_majority": "Pashtun/Hazara",
    },
    "Badakhshan": {
        "capital": "Fayzabad",
        "population": 1_000_000,
        "area_km2": 44_059,
        "districts": 28,
        "latitude": 37.1167,
        "longitude": 70.5833,
        "security_level": "medium",
        "humanitarian_need": "high",
        "border_province": True,
        "ethnic_majority": "Tajik",
    },
    "Paktia": {
        "capital": "Gardez",
        "population": 600_000,
        "area_km2": 6_432,
        "districts": 11,
        "latitude": 33.6000,
        "longitude": 69.2167,
        "security_level": "high",
        "humanitarian_need": "medium",
        "border_province": True,
        "ethnic_majority": "Pashtun",
    },
}

# Ethnic groups and their primary regions
ETHNIC_GROUPS: dict[str, dict[str, Any]] = {
    "Pashtun": {
        "population_pct": 42,
        "primary_regions": ["Kandahar", "Helmand", "Nangarhar", "Paktia", "Khost", "Ghazni"],
        "languages": ["Pashto"],
    },
    "Tajik": {
        "population_pct": 27,
        "primary_regions": ["Kabul", "Herat", "Badakhshan", "Panjshir", "Kapisa"],
        "languages": ["Dari"],
    },
    "Hazara": {
        "population_pct": 9,
        "primary_regions": ["Bamyan", "Daykundi", "Ghazni", "Wardak"],
        "languages": ["Dari (Hazaragi)"],
    },
    "Uzbek": {
        "population_pct": 9,
        "primary_regions": ["Balkh", "Jowzjan", "Faryab", "Sar-e Pul"],
        "languages": ["Uzbek", "Dari"],
    },
    "Turkmen": {
        "population_pct": 3,
        "primary_regions": ["Faryab", "Jowzjan", "Badghis"],
        "languages": ["Turkmen", "Dari"],
    },
    "Aimaq": {
        "population_pct": 4,
        "primary_regions": ["Ghor", "Badghis", "Herat"],
        "languages": ["Dari (Aimaq)"],
    },
    "Baloch": {
        "population_pct": 2,
        "primary_regions": ["Nimroz", "Helmand", "Farah"],
        "languages": ["Balochi", "Pashto"],
    },
    "Nuristani": {
        "population_pct": 1,
        "primary_regions": ["Nuristan", "Kunar"],
        "languages": ["Nuristani languages"],
    },
    "Pashai": {
        "population_pct": 1,
        "primary_regions": ["Laghman", "Nangarhar", "Kunar"],
        "languages": ["Pashai", "Dari"],
    },
}

# Known threat groups and their areas of operation
THREAT_GROUPS: dict[str, dict[str, Any]] = {
    "Taliban": {
        "type": "insurgent",
        "areas_of_operation": ["Kandahar", "Helmand", "Nangarhar", "Kunduz", "Ghazni", "Farah"],
        "estimated_strength": "60000-80000",
        "threat_level": "critical",
        "tactics": ["IED", "ambush", "assassination", "checkpoint attack"],
    },
    "ISIS-K": {
        "type": "terrorist",
        "areas_of_operation": ["Nangarhar", "Kunar", "Kabul"],
        "estimated_strength": "2000-4000",
        "threat_level": "high",
        "tactics": ["suicide bombing", "mass casualty attack", "assassination"],
    },
    "Haqqani Network": {
        "type": "insurgent",
        "areas_of_operation": ["Paktia", "Paktika", "Khost", "Kabul"],
        "estimated_strength": "3000-5000",
        "threat_level": "critical",
        "tactics": ["complex attack", "kidnapping", "IED", "assassination"],
    },
    "IMU": {
        "type": "terrorist",
        "areas_of_operation": ["Kunduz", "Takhar", "Badakhshan"],
        "estimated_strength": "500-1000",
        "threat_level": "medium",
        "tactics": ["armed assault", "IED"],
    },
}

# Humanitarian data
HUMANITARIAN_DATA: dict[str, Any] = {
    "total_population": 40_000_000,
    "internally_displaced": 3_500_000,
    "refugees_abroad": 2_700_000,
    "food_insecure": 19_000_000,
    "acute_food_insecure": 6_000_000,
    "children_acute_malnutrition": 3_200_000,
    "people_need_assistance": 24_400_000,
    "conflict_affected": 5_500_000,
    "natural_disaster_affected": 1_200_000,
}

# Infrastructure data
INFRASTRUCTURE: dict[str, Any] = {
    "roads": {
        "total_km": 42_000,
        "paved_km": 12_000,
        "ring_road_km": 2_210,
    },
    "airports": {
        "international": 4,
        "domestic": 12,
        "military": 8,
    },
    "hospitals": {
        "total": 189,
        "functional": 143,
        "beds_per_10k": 5,
    },
    "schools": {
        "total": 18_000,
        "functional": 15_200,
        "students": 9_500_000,
    },
    "electricity": {
        "access_pct": 35,
        "urban_access_pct": 90,
        "rural_access_pct": 15,
    },
}

# Historical incidents for scenario replay
HISTORICAL_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "tora_bora_2001",
        "name": "Battle of Tora Bora",
        "start_date": "2001-12-12",
        "end_date": "2001-12-17",
        "location": {"lat": 34.0833, "lon": 70.1500},
        "province": "Nangarhar",
        "description": "Coalition and Afghan forces assault on al-Qaeda positions in the White Mountains",
        "forces_friendly": 2500,
        "forces_enemy": 1500,
        "outcome": "partial_success",
    },
    {
        "id": "kunduz_2015",
        "name": "Fall of Kunduz (2015)",
        "start_date": "2015-09-28",
        "end_date": "2015-10-13",
        "location": {"lat": 36.7286, "lon": 68.8578},
        "province": "Kunduz",
        "description": "Taliban temporary capture of Kunduz city, first provincial capital since 2001",
        "forces_friendly": 7000,
        "forces_enemy": 1000,
        "outcome": "city_recaptured",
    },
    {
        "id": "helmand_2010",
        "name": "Operation Moshtarak",
        "start_date": "2010-02-13",
        "end_date": "2010-12-31",
        "location": {"lat": 31.5830, "lon": 64.3639},
        "province": "Helmand",
        "description": "Joint Afghan-ISAF operation to clear Marjah district",
        "forces_friendly": 15000,
        "forces_enemy": 1500,
        "outcome": "success",
    },
    {
        "id": "kabul_airport_2021",
        "name": "Kabul Airport Evacuation",
        "start_date": "2021-08-14",
        "end_date": "2021-08-31",
        "location": {"lat": 34.5658, "lon": 69.2125},
        "province": "Kabul",
        "description": "Mass evacuation during Taliban takeover",
        "evacuees": 124000,
        "outcome": "completed",
    },
]

# Natural disaster history
DISASTER_HISTORY: list[dict[str, Any]] = [
    {
        "type": "earthquake",
        "date": "2022-06-22",
        "location": {"lat": 33.0833, "lon": 69.4667},
        "province": "Paktika",
        "magnitude": 5.9,
        "casualties": 1150,
        "affected": 362000,
    },
    {
        "type": "earthquake",
        "date": "2023-10-07",
        "location": {"lat": 34.3500, "lon": 62.2000},
        "province": "Herat",
        "magnitude": 6.3,
        "casualties": 2400,
        "affected": 275000,
    },
    {
        "type": "flood",
        "date": "2022-08-15",
        "location": {"lat": 35.0167, "lon": 69.1667},
        "province": "Parwan",
        "casualties": 182,
        "affected": 8000,
    },
    {
        "type": "drought",
        "date": "2021-01-01",
        "provinces": ["Balkh", "Jawzjan", "Faryab", "Badghis", "Herat"],
        "affected": 3000000,
        "livestock_lost": 1200000,
    },
    {
        "type": "avalanche",
        "date": "2015-02-25",
        "location": {"lat": 35.3167, "lon": 69.0333},
        "province": "Panjshir",
        "casualties": 310,
    },
]


def get_all_locations() -> list[GeoLocation]:
    """Get all geographic locations."""
    return MAJOR_CITIES + BORDER_CROSSINGS + STRATEGIC_LOCATIONS


def get_province_center(province_name: str) -> tuple[float, float] | None:
    """Get the center coordinates for a province."""
    data = PROVINCE_DATA.get(province_name)
    if data:
        return (data["latitude"], data["longitude"])
    return None


def get_high_risk_provinces() -> list[str]:
    """Get list of high-risk provinces."""
    return [
        name for name, data in PROVINCE_DATA.items()
        if data.get("security_level") in ["high", "critical"]
    ]


def get_border_provinces() -> list[str]:
    """Get list of provinces on international borders."""
    return [
        name for name, data in PROVINCE_DATA.items()
        if data.get("border_province", False)
    ]
