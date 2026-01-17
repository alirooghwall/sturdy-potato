# Afghanistan ISR Platform - API Contracts

## 1. Overview

This document defines the REST and GraphQL API contracts for the Afghanistan ISR Simulation & Analysis Platform. All APIs follow OpenAPI 3.1 specification and implement consistent patterns for authentication, pagination, error handling, and versioning.

## 2. API Conventions

### 2.1 Base URLs

```
Production:    https://api.isr-platform.mil/v1
Staging:       https://api-staging.isr-platform.mil/v1
Development:   https://api-dev.isr-platform.mil/v1
```

### 2.2 Authentication

All API requests require Bearer token authentication via OAuth 2.0:

```http
Authorization: Bearer <access_token>
X-Request-ID: <uuid>
X-Correlation-ID: <uuid>
```

### 2.3 Standard Response Format

```json
{
  "data": { },
  "meta": {
    "requestId": "uuid",
    "timestamp": "ISO8601",
    "pagination": {
      "page": 1,
      "pageSize": 50,
      "totalItems": 1000,
      "totalPages": 20
    }
  },
  "links": {
    "self": "url",
    "next": "url",
    "prev": "url"
  }
}
```

### 2.4 Error Response Format

```json
{
  "error": {
    "code": "ISR-4001",
    "message": "Human readable message",
    "details": [
      {
        "field": "fieldName",
        "issue": "specific validation error"
      }
    ],
    "traceId": "uuid"
  }
}
```

---

## 3. Data Ingestion APIs

### 3.1 Satellite Imagery Ingestion

#### POST /ingestion/satellite/imagery

Upload satellite imagery for processing.

**Request:**
```http
POST /v1/ingestion/satellite/imagery
Content-Type: multipart/form-data

{
  "file": <binary>,
  "metadata": {
    "sensor": "WorldView-3",
    "captureTime": "2026-01-15T08:30:00Z",
    "boundingBox": {
      "north": 34.5553,
      "south": 34.4553,
      "east": 69.2075,
      "west": 69.1075
    },
    "resolution": 0.31,
    "bandType": "MULTISPECTRAL",
    "cloudCover": 5.2,
    "classification": "UNCLASSIFIED"
  }
}
```

**Response (202 Accepted):**
```json
{
  "data": {
    "ingestionId": "img-2026-01-15-001234",
    "status": "QUEUED",
    "estimatedProcessingTime": "PT5M"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-01-15T08:35:00Z"
  },
  "links": {
    "status": "/v1/ingestion/satellite/imagery/img-2026-01-15-001234/status",
    "result": "/v1/ingestion/satellite/imagery/img-2026-01-15-001234"
  }
}
```

### 3.2 OSINT Feed Registration

#### POST /ingestion/osint/feeds

Register a new OSINT data feed.

**Request:**
```json
{
  "feedName": "Afghan Local News Dari",
  "feedType": "RSS",
  "sourceUrl": "https://example-news.af/rss/dari",
  "language": "prs",
  "updateFrequency": "PT15M",
  "credibilityRating": 0.75,
  "categories": ["NEWS", "LOCAL", "SECURITY"],
  "processingConfig": {
    "enableTranslation": true,
    "enableEntityExtraction": true,
    "enableSentiment": true,
    "targetLanguages": ["en"]
  }
}
```

**Response (201 Created):**
```json
{
  "data": {
    "feedId": "feed-osint-20260115-001",
    "status": "ACTIVE",
    "lastPolled": null,
    "nextPoll": "2026-01-15T08:50:00Z",
    "totalItemsProcessed": 0
  }
}
```

### 3.3 Cyber Telemetry Ingestion

#### POST /ingestion/cyber/indicators

Ingest cyber threat indicators.

**Request:**
```json
{
  "indicators": [
    {
      "type": "IP_ADDRESS",
      "value": "192.168.1.100",
      "threatType": "C2_SERVER",
      "confidence": 0.92,
      "firstSeen": "2026-01-10T12:00:00Z",
      "lastSeen": "2026-01-15T08:00:00Z",
      "source": "IDS-SENSOR-KABUL-01",
      "tags": ["APT", "COBALT_STRIKE"],
      "stixBundle": "<base64_encoded_stix>"
    }
  ],
  "batchId": "batch-cyber-20260115-001"
}
```

**Response (202 Accepted):**
```json
{
  "data": {
    "batchId": "batch-cyber-20260115-001",
    "indicatorsReceived": 1,
    "indicatorsValid": 1,
    "indicatorsDuplicate": 0,
    "status": "PROCESSING"
  }
}
```

---

## 4. Analytics APIs

### 4.1 Sensor Fusion

#### GET /analytics/fusion/tracks

Retrieve fused entity tracks.

**Request:**
```http
GET /v1/analytics/fusion/tracks?
    boundingBox=34.4,69.1,34.6,69.3&
    startTime=2026-01-15T00:00:00Z&
    endTime=2026-01-15T23:59:59Z&
    entityTypes=VEHICLE,PERSONNEL&
    minConfidence=0.7&
    page=1&
    pageSize=50
```

**Response:**
```json
{
  "data": {
    "tracks": [
      {
        "trackId": "track-2026-01-15-00001",
        "entityType": "VEHICLE",
        "entitySubtype": "TECHNICAL",
        "currentPosition": {
          "latitude": 34.5234,
          "longitude": 69.1723,
          "altitude": 1850,
          "timestamp": "2026-01-15T14:30:00Z",
          "accuracy": 5.0
        },
        "velocity": {
          "speed": 45.2,
          "heading": 270,
          "unit": "KPH"
        },
        "confidence": 0.89,
        "contributingSources": [
          {
            "sourceType": "SATELLITE",
            "sourceId": "sat-wv3-001",
            "weight": 0.4
          },
          {
            "sourceType": "UAV_EO",
            "sourceId": "uav-scan-eagle-003",
            "weight": 0.35
          },
          {
            "sourceType": "SIGINT",
            "sourceId": "sigint-cell-intercept",
            "weight": 0.25
          }
        ],
        "attributes": {
          "estimatedOccupants": 4,
          "weaponsVisible": true,
          "associatedGroup": "UNK_INSURGENT_CELL_A"
        },
        "history": [
          {
            "timestamp": "2026-01-15T14:00:00Z",
            "latitude": 34.5100,
            "longitude": 69.1500
          }
        ]
      }
    ]
  },
  "meta": {
    "pagination": {
      "page": 1,
      "pageSize": 50,
      "totalItems": 127,
      "totalPages": 3
    }
  }
}
```

### 4.2 Anomaly Detection

#### GET /analytics/anomalies

Retrieve detected anomalies.

**Request:**
```http
GET /v1/analytics/anomalies?
    domain=GEO_MOVEMENT&
    severity=HIGH,CRITICAL&
    startTime=2026-01-14T00:00:00Z&
    endTime=2026-01-15T23:59:59Z&
    region=KANDAHAR
```

**Response:**
```json
{
  "data": {
    "anomalies": [
      {
        "anomalyId": "anom-geo-20260115-0042",
        "domain": "GEO_MOVEMENT",
        "subtype": "UNUSUAL_ROUTE_ACTIVITY",
        "severity": "HIGH",
        "severityScore": 82,
        "detectedAt": "2026-01-15T03:45:00Z",
        "location": {
          "type": "Feature",
          "geometry": {
            "type": "LineString",
            "coordinates": [[69.12, 34.45], [69.18, 34.52], [69.25, 34.48]]
          },
          "properties": {
            "region": "KANDAHAR",
            "routeName": "SMUGGLING_ROUTE_K7"
          }
        },
        "description": "Unusual nighttime vehicle activity detected on known smuggling route. 847% increase over 30-day baseline.",
        "baseline": {
          "period": "30_DAYS",
          "averageCount": 3.2,
          "observedCount": 27
        },
        "relatedEntities": [
          {
            "trackId": "track-2026-01-15-00089",
            "role": "PRIMARY_ACTOR"
          }
        ],
        "modelInfo": {
          "modelId": "isolation-forest-geo-v3",
          "modelVersion": "3.2.1",
          "anomalyScore": 0.94
        }
      }
    ]
  }
}
```

### 4.3 Threat Scoring

#### POST /analytics/threat-score

Calculate threat score for an entity or situation.

**Request:**
```json
{
  "entityId": "entity-insurgent-cell-alpha-7",
  "contextWindow": {
    "startTime": "2026-01-01T00:00:00Z",
    "endTime": "2026-01-15T23:59:59Z"
  },
  "factorOverrides": {
    "credibilityBoost": 0.1
  },
  "includeExplanation": true
}
```

**Response:**
```json
{
  "data": {
    "entityId": "entity-insurgent-cell-alpha-7",
    "overallScore": 78,
    "category": "HIGH",
    "categoryThresholds": {
      "LOW": [0, 30],
      "MEDIUM": [31, 60],
      "HIGH": [61, 85],
      "CRITICAL": [86, 100]
    },
    "factorScores": {
      "credibility": {
        "score": 85,
        "weight": 0.20,
        "contribution": 17,
        "details": "Multiple corroborated HUMINT reports (3), satellite imagery confirmation"
      },
      "tacticalImpact": {
        "score": 72,
        "weight": 0.25,
        "contribution": 18,
        "details": "Proximity to Kandahar city center (12km), near main supply route"
      },
      "capability": {
        "score": 68,
        "weight": 0.20,
        "contribution": 13.6,
        "details": "Estimated 15-20 fighters, light weapons, possible IED capability"
      },
      "vulnerability": {
        "score": 80,
        "weight": 0.20,
        "contribution": 16,
        "details": "Target area has limited security presence, civilian population exposed"
      },
      "timeSensitivity": {
        "score": 65,
        "weight": 0.15,
        "contribution": 9.75,
        "details": "Increased chatter suggests planning phase, no imminent timeline"
      }
    },
    "explanation": {
      "summary": "High threat level due to confirmed insurgent presence near populated area with limited security coverage. Recent intelligence indicates active planning.",
      "keyIndicators": [
        "3 HUMINT reports in last 7 days mentioning this cell",
        "Satellite detected new encampment 15km from Kandahar",
        "SIGINT intercept referencing 'upcoming operation'"
      ],
      "recommendations": [
        "Increase ISR coverage of grid reference KAF-2234",
        "Coordinate with local security forces for area patrol",
        "Monitor social media for propaganda activity"
      ]
    },
    "trend": {
      "direction": "INCREASING",
      "changePercent": 12,
      "periodDays": 7
    },
    "calculatedAt": "2026-01-15T15:30:00Z"
  }
}
```

### 4.4 Explainability Query

#### POST /analytics/explain

Get explanation for any AI/ML decision.

**Request:**
```json
{
  "predictionId": "pred-threat-20260115-00234",
  "explanationType": "NATURAL_LANGUAGE",
  "detailLevel": "DETAILED",
  "includeCounterfactuals": true
}
```

**Response:**
```json
{
  "data": {
    "predictionId": "pred-threat-20260115-00234",
    "originalPrediction": {
      "type": "THREAT_SCORE",
      "value": 78,
      "confidence": 0.87
    },
    "explanation": {
      "naturalLanguage": "The threat score of 78 (HIGH) was primarily driven by: (1) High source credibility from 3 independent HUMINT reports that corroborate insurgent presence, (2) Geographic proximity to Kandahar city center increasing potential civilian impact, and (3) Recent SIGINT intercepts indicating active operational planning. The score increased 12% over the past week due to the new satellite imagery confirmation.",
      "featureImportance": [
        {
          "feature": "humint_report_count_7d",
          "value": 3,
          "importance": 0.28,
          "direction": "POSITIVE"
        },
        {
          "feature": "distance_to_population_center_km",
          "value": 12,
          "importance": 0.22,
          "direction": "POSITIVE"
        },
        {
          "feature": "sigint_activity_score",
          "value": 0.75,
          "importance": 0.18,
          "direction": "POSITIVE"
        }
      ],
      "counterfactuals": [
        {
          "scenario": "If distance to population center were > 50km",
          "predictedScore": 58,
          "category": "MEDIUM"
        },
        {
          "scenario": "If HUMINT reports were not corroborated",
          "predictedScore": 52,
          "category": "MEDIUM"
        }
      ]
    },
    "modelInfo": {
      "modelId": "threat-scorer-ensemble-v4",
      "modelVersion": "4.1.2",
      "explainerType": "SHAP_TREE"
    }
  }
}
```

---

## 5. Simulation APIs

### 5.1 Scenario Management

#### POST /simulation/scenarios

Create a new simulation scenario.

**Request:**
```json
{
  "name": "Border Incursion Scenario Alpha",
  "description": "Simulated border crossing incident with insurgent forces",
  "type": "WHAT_IF",
  "baselineDate": "2026-01-15T00:00:00Z",
  "duration": {
    "value": 72,
    "unit": "HOURS"
  },
  "region": {
    "type": "Polygon",
    "coordinates": [[[69.0, 34.0], [70.0, 34.0], [70.0, 35.0], [69.0, 35.0], [69.0, 34.0]]]
  },
  "initialConditions": {
    "agents": [
      {
        "agentType": "INSURGENT_CELL",
        "count": 3,
        "averageSize": 15,
        "initialLocations": "RANDOM_BORDER_ZONE",
        "behavior": "INFILTRATION_TTP"
      },
      {
        "agentType": "BORDER_PATROL",
        "count": 5,
        "averageSize": 8,
        "initialLocations": "CHECKPOINT_POSITIONS",
        "behavior": "PATROL_STANDARD"
      }
    ],
    "environment": {
      "weatherPattern": "WINTER_CLEAR",
      "visibility": "GOOD",
      "moonPhase": 0.25
    }
  },
  "objectives": [
    {
      "id": "obj-1",
      "description": "Assess detection probability",
      "metrics": ["DETECTION_RATE", "TIME_TO_DETECTION", "FALSE_ALARM_RATE"]
    }
  ],
  "stochasticRuns": 100
}
```

**Response (201 Created):**
```json
{
  "data": {
    "scenarioId": "scenario-2026-01-15-alpha-001",
    "status": "CREATED",
    "estimatedRuntime": "PT45M",
    "computeResources": {
      "gpuNodes": 4,
      "cpuCores": 64,
      "memoryGB": 256
    }
  }
}
```

#### POST /simulation/scenarios/{scenarioId}/run

Execute a simulation scenario.

**Request:**
```json
{
  "executionMode": "BATCH",
  "priority": "NORMAL",
  "outputConfig": {
    "saveInterval": "PT5M",
    "includeAgentTraces": true,
    "includeHeatmaps": true,
    "videoOutput": false
  }
}
```

**Response (202 Accepted):**
```json
{
  "data": {
    "runId": "run-2026-01-15-alpha-001-001",
    "status": "QUEUED",
    "queuePosition": 3,
    "estimatedStart": "2026-01-15T16:00:00Z"
  }
}
```

#### GET /simulation/scenarios/{scenarioId}/runs/{runId}/results

Get simulation results.

**Response:**
```json
{
  "data": {
    "runId": "run-2026-01-15-alpha-001-001",
    "status": "COMPLETED",
    "completedAt": "2026-01-15T16:48:00Z",
    "summary": {
      "totalAgentsSimulated": 165,
      "totalEvents": 4523,
      "simulatedDuration": "PT72H"
    },
    "metrics": {
      "DETECTION_RATE": {
        "mean": 0.73,
        "std": 0.12,
        "min": 0.45,
        "max": 0.92,
        "percentiles": {
          "p25": 0.65,
          "p50": 0.74,
          "p75": 0.82
        }
      },
      "TIME_TO_DETECTION": {
        "mean": 3.2,
        "unit": "HOURS",
        "std": 1.8
      },
      "FALSE_ALARM_RATE": {
        "mean": 0.08,
        "std": 0.03
      }
    },
    "insights": [
      {
        "type": "VULNERABILITY",
        "description": "Grid sector KAF-2234 shows 40% lower detection rate due to terrain masking",
        "recommendation": "Consider additional sensor placement or patrol route adjustment"
      }
    ],
    "artifacts": {
      "heatmapUrl": "/v1/simulation/artifacts/run-2026-01-15-alpha-001-001/heatmap.geojson",
      "agentTracesUrl": "/v1/simulation/artifacts/run-2026-01-15-alpha-001-001/traces.parquet",
      "eventLogUrl": "/v1/simulation/artifacts/run-2026-01-15-alpha-001-001/events.jsonl"
    }
  }
}
```

### 5.2 Disaster Modeling

#### POST /simulation/disaster/earthquake

Run earthquake impact simulation.

**Request:**
```json
{
  "epicenter": {
    "latitude": 36.7,
    "longitude": 71.3
  },
  "magnitude": 6.8,
  "depth": 15,
  "depthUnit": "KM",
  "faultMechanism": "THRUST",
  "assessmentConfig": {
    "includeBuildings": true,
    "includeCasualties": true,
    "includeInfrastructure": true,
    "populationDataset": "AFGHANISTAN_2025_CENSUS",
    "buildingVulnerabilityModel": "CAPRA_AFGHAN_V2"
  }
}
```

**Response:**
```json
{
  "data": {
    "simulationId": "eq-sim-20260115-001",
    "status": "COMPLETED",
    "results": {
      "groundMotion": {
        "peakGroundAcceleration": {
          "max": 0.45,
          "unit": "G",
          "affectedArea": {
            "type": "Feature",
            "geometry": {
              "type": "Polygon",
              "coordinates": [/* ... */]
            }
          }
        },
        "intensityMap": "/v1/simulation/artifacts/eq-sim-20260115-001/intensity.geotiff"
      },
      "impact": {
        "populationExposed": {
          "total": 2450000,
          "byIntensity": {
            "VI": 1200000,
            "VII": 800000,
            "VIII": 350000,
            "IX": 100000
          }
        },
        "casualties": {
          "estimated": {
            "fatalities": {
              "mean": 2100,
              "p10": 1200,
              "p90": 4500
            },
            "injuries": {
              "mean": 8500,
              "p10": 5000,
              "p90": 15000
            }
          },
          "uncertaintyNote": "Estimates based on building stock vulnerability models"
        },
        "buildingDamage": {
          "total": 145000,
          "byCategory": {
            "COLLAPSED": 12000,
            "SEVERE": 28000,
            "MODERATE": 45000,
            "LIGHT": 60000
          }
        },
        "infrastructureDamage": {
          "roadsKmAffected": 450,
          "bridgesAffected": 23,
          "healthFacilitiesAffected": 45,
          "schoolsAffected": 120
        }
      },
      "responseNeeds": {
        "searchAndRescue": {
          "priorityZones": [/* GeoJSON features */],
          "estimatedTrappedPersons": 3500
        },
        "medicalSurge": {
          "hospitalCapacityGap": 4200,
          "bloodUnitsNeeded": 8500
        },
        "shelter": {
          "displacedPopulation": 180000,
          "temporarySheltersNeeded": 45000
        }
      }
    }
  }
}
```

### 5.3 Logistics Optimization

#### POST /simulation/logistics/optimize

Optimize relief logistics.

**Request:**
```json
{
  "disasterScenarioId": "eq-sim-20260115-001",
  "resources": {
    "warehouses": [
      {
        "id": "wh-kabul-main",
        "location": {"lat": 34.52, "lon": 69.17},
        "inventory": {
          "TENTS": 5000,
          "BLANKETS": 20000,
          "FOOD_KITS": 15000,
          "WATER_LITERS": 500000,
          "MEDICAL_KITS": 2000
        }
      }
    ],
    "vehicles": [
      {
        "type": "TRUCK_10T",
        "count": 50,
        "baseLocation": "wh-kabul-main"
      },
      {
        "type": "HELICOPTER_MI17",
        "count": 8,
        "baseLocation": "airbase-bagram"
      }
    ]
  },
  "constraints": {
    "maxDeliveryTime": 72,
    "timeUnit": "HOURS",
    "roadConditions": "POST_EARTHQUAKE",
    "securityZones": ["avoid-zone-1", "avoid-zone-2"]
  },
  "objectives": {
    "primary": "MINIMIZE_UNMET_NEEDS",
    "secondary": "MINIMIZE_COST"
  }
}
```

**Response:**
```json
{
  "data": {
    "optimizationId": "logistics-opt-20260115-001",
    "status": "OPTIMAL_FOUND",
    "solution": {
      "routes": [
        {
          "vehicleId": "truck-001",
          "departure": "2026-01-15T18:00:00Z",
          "stops": [
            {
              "location": {"lat": 36.5, "lon": 71.1},
              "arrivalTime": "2026-01-16T04:00:00Z",
              "delivery": {"TENTS": 200, "FOOD_KITS": 500}
            }
          ],
          "totalDistance": 320,
          "distanceUnit": "KM"
        }
      ],
      "coverage": {
        "populationServed": 165000,
        "populationUnserved": 15000,
        "coveragePercent": 91.7
      },
      "resourceUtilization": {
        "vehicleUtilization": 0.87,
        "inventoryDepletion": {
          "TENTS": 0.92,
          "FOOD_KITS": 0.88
        }
      }
    },
    "alternativeSolutions": [
      {
        "description": "Prioritize speed over cost",
        "coveragePercent": 95.2,
        "additionalCost": 125000
      }
    ]
  }
}
```

---

## 6. Information Warfare APIs

### 6.1 Narrative Analysis

#### GET /narrative/themes

Get current narrative themes.

**Request:**
```http
GET /v1/narrative/themes?
    region=AFGHANISTAN&
    startDate=2026-01-01&
    endDate=2026-01-15&
    minMentions=100
```

**Response:**
```json
{
  "data": {
    "themes": [
      {
        "themeId": "theme-taliban-legitimacy-2026",
        "name": "Taliban Governance Legitimacy",
        "description": "Narratives around Taliban's right to rule and international recognition",
        "sentiment": {
          "overall": -0.15,
          "trend": "STABLE"
        },
        "volume": {
          "totalMentions": 45230,
          "uniqueSources": 1250,
          "peakDate": "2026-01-12"
        },
        "subThemes": [
          {
            "name": "International Recognition",
            "mentions": 12000
          },
          {
            "name": "Domestic Support",
            "mentions": 18000
          },
          {
            "name": "Human Rights Criticism",
            "mentions": 15230
          }
        ],
        "topSources": [
          {
            "sourceType": "STATE_MEDIA",
            "count": 8500,
            "sentiment": 0.65
          },
          {
            "sourceType": "INTERNATIONAL_NEWS",
            "count": 22000,
            "sentiment": -0.45
          }
        ],
        "geographicDistribution": {
          "AFGHANISTAN": 0.45,
          "PAKISTAN": 0.20,
          "IRAN": 0.10,
          "GLOBAL": 0.25
        }
      }
    ]
  }
}
```

### 6.2 Disinformation Detection

#### POST /narrative/disinformation/analyze

Analyze content for disinformation indicators.

**Request:**
```json
{
  "content": {
    "text": "Breaking: International aid organizations confirm Taliban has successfully eliminated all poverty in Afghanistan...",
    "sourceUrl": "https://suspicious-news.example.com/article/12345",
    "publishedAt": "2026-01-15T10:00:00Z",
    "language": "en"
  },
  "analysisConfig": {
    "checkFactualClaims": true,
    "analyzeSourceCredibility": true,
    "detectCoordinatedBehavior": true,
    "crossReferenceVerified": true
  }
}
```

**Response:**
```json
{
  "data": {
    "analysisId": "disinfo-analysis-20260115-00234",
    "overallScore": {
      "disinformationLikelihood": 0.89,
      "confidence": 0.82,
      "category": "LIKELY_DISINFORMATION"
    },
    "factualAnalysis": {
      "claims": [
        {
          "claim": "International aid organizations confirm poverty elimination",
          "verdict": "FALSE",
          "confidence": 0.95,
          "evidence": [
            {
              "source": "UN OCHA Report 2026-01",
              "quote": "Afghanistan remains one of world's poorest nations with 97% below poverty line",
              "url": "https://reliefweb.int/report/..."
            }
          ]
        }
      ]
    },
    "sourceCredibility": {
      "domainAge": "32 days",
      "historicalAccuracy": null,
      "knownAffiliations": ["PROPAGANDA_NETWORK_A"],
      "credibilityScore": 0.12
    },
    "coordinationSignals": {
      "detected": true,
      "indicators": [
        {
          "type": "SYNCHRONIZED_POSTING",
          "description": "23 accounts shared this within 5 minutes of publication",
          "accounts": ["list-truncated"]
        },
        {
          "type": "BOT_AMPLIFICATION",
          "description": "68% of early shares from accounts with bot-like behavior",
          "botScore": 0.78
        }
      ],
      "estimatedReach": 125000,
      "viralPotential": "MEDIUM"
    },
    "recommendations": [
      {
        "action": "FLAG_FOR_REVIEW",
        "priority": "HIGH"
      },
      {
        "action": "MONITOR_SPREAD",
        "reason": "Track if narrative gains traction"
      }
    ]
  }
}
```

### 6.3 Campaign Tracking

#### GET /narrative/campaigns/{campaignId}

Track an identified disinformation campaign.

**Response:**
```json
{
  "data": {
    "campaignId": "campaign-taliban-eco-disinfo-2026",
    "name": "Taliban Economic Success Campaign",
    "status": "ACTIVE",
    "firstDetected": "2026-01-05T00:00:00Z",
    "summary": "Coordinated campaign promoting false economic achievements",
    "metrics": {
      "totalPosts": 4523,
      "uniqueAccounts": 234,
      "estimatedReach": 2500000,
      "engagementRate": 0.034
    },
    "actors": {
      "identifiedAccounts": 89,
      "suspectedBots": 145,
      "linkedToKnownNetworks": ["troll-farm-pak-01", "state-media-network"]
    },
    "narratives": [
      {
        "narrative": "Poverty eliminated",
        "frequency": 1200
      },
      {
        "narrative": "Economic growth",
        "frequency": 980
      }
    ],
    "platforms": {
      "TWITTER": 0.45,
      "FACEBOOK": 0.30,
      "TELEGRAM": 0.20,
      "OTHER": 0.05
    },
    "timeline": [
      {
        "date": "2026-01-05",
        "posts": 45,
        "reach": 50000
      },
      {
        "date": "2026-01-06",
        "posts": 120,
        "reach": 150000
      }
    ]
  }
}
```

---

## 7. Alerting APIs

### 7.1 Alert Management

#### GET /alerts

Retrieve alerts.

**Request:**
```http
GET /v1/alerts?
    severity=HIGH,CRITICAL&
    status=OPEN,ACKNOWLEDGED&
    category=SECURITY,HUMANITARIAN&
    region=KANDAHAR,KABUL&
    page=1&
    pageSize=20
```

**Response:**
```json
{
  "data": {
    "alerts": [
      {
        "alertId": "alert-20260115-sec-00234",
        "title": "Major Border Activity Detected",
        "severity": "HIGH",
        "category": "SECURITY",
        "subcategory": "BORDER_INCURSION",
        "status": "OPEN",
        "createdAt": "2026-01-15T03:45:00Z",
        "updatedAt": "2026-01-15T14:30:00Z",
        "region": "SPIN_BOLDAK",
        "location": {
          "latitude": 31.0053,
          "longitude": 66.3984
        },
        "summary": "Unusual nighttime movement detected at Spin Boldak border crossing. 15+ vehicles observed moving without customs clearance.",
        "threatScore": 76,
        "confidence": 0.84,
        "sources": [
          {
            "type": "SATELLITE",
            "timestamp": "2026-01-15T02:30:00Z"
          },
          {
            "type": "SIGINT",
            "timestamp": "2026-01-15T03:15:00Z"
          }
        ],
        "relatedEntities": [
          {
            "entityId": "track-2026-01-15-00089",
            "type": "VEHICLE_CONVOY"
          }
        ],
        "assignedTo": "analyst-team-kandahar",
        "sla": {
          "responseDeadline": "2026-01-15T05:45:00Z",
          "status": "OVERDUE"
        }
      }
    ]
  }
}
```

#### POST /alerts/{alertId}/acknowledge

Acknowledge an alert.

**Request:**
```json
{
  "acknowledgement": {
    "analystId": "analyst-jdoe",
    "notes": "Reviewing satellite imagery and coordinating with border security",
    "estimatedResolutionTime": "2026-01-15T18:00:00Z"
  }
}
```

**Response:**
```json
{
  "data": {
    "alertId": "alert-20260115-sec-00234",
    "status": "ACKNOWLEDGED",
    "acknowledgedAt": "2026-01-15T14:35:00Z",
    "acknowledgedBy": "analyst-jdoe"
  }
}
```

### 7.2 Alert Configuration

#### POST /alerts/rules

Create alert rule.

**Request:**
```json
{
  "ruleName": "High-Value Target Movement",
  "description": "Alert when known HVT associated tracks are detected",
  "enabled": true,
  "conditions": {
    "operator": "AND",
    "rules": [
      {
        "field": "entityType",
        "operator": "IN",
        "value": ["HVT", "HVT_ASSOCIATE"]
      },
      {
        "field": "confidence",
        "operator": ">=",
        "value": 0.7
      },
      {
        "field": "movementType",
        "operator": "==",
        "value": "ACTIVE"
      }
    ]
  },
  "actions": [
    {
      "type": "CREATE_ALERT",
      "config": {
        "severity": "CRITICAL",
        "category": "SECURITY"
      }
    },
    {
      "type": "NOTIFY",
      "config": {
        "channels": ["EMAIL", "SMS", "DASHBOARD"],
        "recipients": ["hvt-response-team"]
      }
    },
    {
      "type": "INCREASE_ISR",
      "config": {
        "radiusKm": 25,
        "duration": "PT6H"
      }
    }
  ],
  "throttle": {
    "maxAlertsPerHour": 5,
    "cooldownMinutes": 30
  }
}
```

---

## 8. Dashboard & Reporting APIs

### 8.1 Dashboard Data

#### GET /dashboard/overview

Get dashboard overview data.

**Response:**
```json
{
  "data": {
    "timestamp": "2026-01-15T15:00:00Z",
    "summary": {
      "activeAlerts": {
        "CRITICAL": 2,
        "HIGH": 8,
        "MEDIUM": 23,
        "LOW": 45
      },
      "activeTracks": 1234,
      "activeSimulations": 3,
      "dataIngestionRate": {
        "eventsPerSecond": 45230,
        "trend": "STABLE"
      }
    },
    "threatOverview": {
      "nationalThreatLevel": "ELEVATED",
      "regionalBreakdown": [
        {
          "region": "KABUL",
          "threatScore": 65,
          "trend": "DECREASING"
        },
        {
          "region": "KANDAHAR",
          "threatScore": 78,
          "trend": "INCREASING"
        },
        {
          "region": "HERAT",
          "threatScore": 52,
          "trend": "STABLE"
        }
      ]
    },
    "recentEvents": [
      {
        "eventId": "evt-20260115-00234",
        "type": "EXPLOSION",
        "location": "Kabul",
        "timestamp": "2026-01-15T12:30:00Z",
        "severity": "HIGH"
      }
    ],
    "narrativeTrends": {
      "topThemes": [
        {"theme": "Security Concerns", "volume": 12340, "sentiment": -0.45},
        {"theme": "Economic Hardship", "volume": 8900, "sentiment": -0.62}
      ],
      "disinformationAlerts": 12
    },
    "systemHealth": {
      "status": "HEALTHY",
      "dataLagSeconds": 15,
      "modelInferenceLatencyMs": 45
    }
  }
}
```

### 8.2 Report Generation

#### POST /reports/generate

Generate intelligence report.

**Request:**
```json
{
  "reportType": "SITUATION_REPORT",
  "parameters": {
    "region": "KANDAHAR",
    "timeRange": {
      "start": "2026-01-14T00:00:00Z",
      "end": "2026-01-15T00:00:00Z"
    },
    "sections": [
      "EXECUTIVE_SUMMARY",
      "THREAT_ASSESSMENT",
      "SIGNIFICANT_EVENTS",
      "HUMANITARIAN_STATUS",
      "FORECAST"
    ],
    "classification": "UNCLASSIFIED",
    "format": "PDF"
  },
  "distribution": {
    "recipients": ["cmd-kandahar@mil.gov", "intel-hq@mil.gov"],
    "sendImmediately": true
  }
}
```

**Response:**
```json
{
  "data": {
    "reportId": "rpt-sitrep-20260115-kandahar-001",
    "status": "GENERATING",
    "estimatedCompletionTime": "2026-01-15T15:10:00Z",
    "previewAvailable": false
  }
}
```

#### GET /reports/{reportId}

Get report status and download.

**Response:**
```json
{
  "data": {
    "reportId": "rpt-sitrep-20260115-kandahar-001",
    "status": "COMPLETED",
    "generatedAt": "2026-01-15T15:08:00Z",
    "metadata": {
      "title": "Kandahar Province Situation Report - 2026-01-14",
      "classification": "UNCLASSIFIED",
      "pageCount": 12,
      "sections": ["EXECUTIVE_SUMMARY", "THREAT_ASSESSMENT", "SIGNIFICANT_EVENTS", "HUMANITARIAN_STATUS", "FORECAST"]
    },
    "downloads": {
      "pdf": "/v1/reports/rpt-sitrep-20260115-kandahar-001/download?format=pdf",
      "html": "/v1/reports/rpt-sitrep-20260115-kandahar-001/download?format=html"
    },
    "distribution": {
      "sentTo": 2,
      "sentAt": "2026-01-15T15:09:00Z"
    }
  }
}
```

---

## 9. Administration APIs

### 9.1 User Management

#### GET /admin/users

List users (admin only).

**Response:**
```json
{
  "data": {
    "users": [
      {
        "userId": "user-analyst-001",
        "username": "jdoe",
        "displayName": "John Doe",
        "email": "jdoe@mil.gov",
        "roles": ["ANALYST", "REPORT_GENERATOR"],
        "organization": "INTEL_HQ",
        "clearanceLevel": "SECRET",
        "status": "ACTIVE",
        "lastLogin": "2026-01-15T14:00:00Z",
        "createdAt": "2025-06-01T00:00:00Z"
      }
    ]
  }
}
```

### 9.2 Audit Logs

#### GET /admin/audit-logs

Retrieve audit logs.

**Request:**
```http
GET /v1/admin/audit-logs?
    userId=user-analyst-001&
    action=DATA_ACCESS,REPORT_GENERATE&
    startTime=2026-01-15T00:00:00Z&
    endTime=2026-01-15T23:59:59Z
```

**Response:**
```json
{
  "data": {
    "logs": [
      {
        "logId": "audit-20260115-00001234",
        "timestamp": "2026-01-15T14:30:00Z",
        "userId": "user-analyst-001",
        "action": "DATA_ACCESS",
        "resource": "/v1/analytics/fusion/tracks",
        "parameters": {
          "boundingBox": "34.4,69.1,34.6,69.3",
          "entityTypes": "VEHICLE"
        },
        "result": "SUCCESS",
        "ipAddress": "10.0.1.50",
        "userAgent": "ISR-Dashboard/2.1.0"
      }
    ]
  }
}
```

---

## 10. GraphQL API

The platform also exposes a GraphQL API for flexible querying:

### Endpoint
```
POST /graphql
```

### Schema (Excerpt)

```graphql
type Query {
  # Tracks and Entities
  tracks(
    boundingBox: BoundingBoxInput
    timeRange: TimeRangeInput
    entityTypes: [EntityType!]
    minConfidence: Float
    pagination: PaginationInput
  ): TrackConnection!
  
  track(id: ID!): Track
  
  # Alerts
  alerts(
    severity: [Severity!]
    status: [AlertStatus!]
    category: [AlertCategory!]
    pagination: PaginationInput
  ): AlertConnection!
  
  alert(id: ID!): Alert
  
  # Narratives
  narrativeThemes(
    region: String
    timeRange: TimeRangeInput
    minMentions: Int
  ): [NarrativeTheme!]!
  
  # Threat Scoring
  threatScore(entityId: ID!): ThreatScore
  
  # Dashboard
  dashboardOverview: DashboardOverview!
}

type Track {
  id: ID!
  entityType: EntityType!
  entitySubtype: String
  currentPosition: Position!
  velocity: Velocity
  confidence: Float!
  contributingSources: [DataSource!]!
  attributes: JSON
  history(limit: Int): [Position!]!
  relatedAlerts: [Alert!]!
  threatScore: ThreatScore
}

type Alert {
  id: ID!
  title: String!
  severity: Severity!
  category: AlertCategory!
  status: AlertStatus!
  createdAt: DateTime!
  location: Position
  summary: String!
  threatScore: Int
  confidence: Float!
  sources: [DataSource!]!
  relatedTracks: [Track!]!
  assignedTo: User
  actions: [AlertAction!]!
}

type ThreatScore {
  entityId: ID!
  overallScore: Int!
  category: ThreatCategory!
  factorScores: [FactorScore!]!
  explanation: Explanation!
  trend: Trend!
  calculatedAt: DateTime!
}

type Mutation {
  # Alert Management
  acknowledgeAlert(id: ID!, notes: String): Alert!
  resolveAlert(id: ID!, resolution: AlertResolutionInput!): Alert!
  
  # Simulation
  createScenario(input: ScenarioInput!): Scenario!
  runScenario(scenarioId: ID!, config: RunConfigInput!): SimulationRun!
  
  # Data Ingestion
  registerOsintFeed(input: OsintFeedInput!): OsintFeed!
  
  # Report Generation
  generateReport(input: ReportInput!): Report!
}

type Subscription {
  # Real-time alerts
  alertCreated(severity: [Severity!], category: [AlertCategory!]): Alert!
  alertUpdated(id: ID): Alert!
  
  # Track updates
  trackUpdated(boundingBox: BoundingBoxInput): Track!
  
  # Threat score changes
  threatScoreChanged(entityId: ID, minScoreChange: Int): ThreatScore!
}
```

### Example GraphQL Query

```graphql
query GetActiveHighPriorityAlerts {
  alerts(
    severity: [HIGH, CRITICAL]
    status: [OPEN, ACKNOWLEDGED]
    pagination: { limit: 10 }
  ) {
    edges {
      node {
        id
        title
        severity
        createdAt
        location {
          latitude
          longitude
        }
        summary
        threatScore
        relatedTracks {
          id
          entityType
          currentPosition {
            latitude
            longitude
          }
        }
        assignedTo {
          displayName
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

---

## 11. WebSocket APIs

### Real-Time Event Streaming

**Endpoint:** `wss://api.isr-platform.mil/v1/ws`

**Connection:**
```javascript
const ws = new WebSocket('wss://api.isr-platform.mil/v1/ws', {
  headers: {
    'Authorization': 'Bearer <token>'
  }
});
```

**Subscribe to channels:**
```json
{
  "action": "subscribe",
  "channels": [
    {
      "type": "alerts",
      "filters": {
        "severity": ["HIGH", "CRITICAL"],
        "region": ["KABUL", "KANDAHAR"]
      }
    },
    {
      "type": "tracks",
      "filters": {
        "boundingBox": [34.4, 69.1, 34.6, 69.3],
        "entityTypes": ["VEHICLE", "PERSONNEL"]
      }
    },
    {
      "type": "threat_scores",
      "filters": {
        "minScore": 70
      }
    }
  ]
}
```

**Event messages:**
```json
{
  "channel": "alerts",
  "event": "alert.created",
  "timestamp": "2026-01-15T15:30:00Z",
  "data": {
    "alertId": "alert-20260115-sec-00235",
    "title": "Suspicious Activity Detected",
    "severity": "HIGH"
  }
}
```

---

## 12. Rate Limiting & Quotas

| Tier | Requests/Min | Burst | WebSocket Connections |
|------|-------------|-------|----------------------|
| Standard Analyst | 100 | 200 | 2 |
| Senior Analyst | 300 | 500 | 5 |
| Operations Center | 1000 | 2000 | 20 |
| System Integration | 5000 | 10000 | 50 |

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705330800
```

---

## 13. Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| ISR-4001 | 400 | Invalid request parameters |
| ISR-4002 | 400 | Invalid GeoJSON format |
| ISR-4003 | 400 | Invalid time range |
| ISR-4010 | 401 | Authentication required |
| ISR-4011 | 401 | Token expired |
| ISR-4030 | 403 | Insufficient permissions |
| ISR-4031 | 403 | Classification level too low |
| ISR-4040 | 404 | Resource not found |
| ISR-4090 | 409 | Conflict - resource already exists |
| ISR-4290 | 429 | Rate limit exceeded |
| ISR-5000 | 500 | Internal server error |
| ISR-5030 | 503 | Service temporarily unavailable |

---

*Document Version: 1.0*  
*Classification: UNCLASSIFIED // FOR OFFICIAL USE ONLY*  
*Last Updated: 2026-01-17*
