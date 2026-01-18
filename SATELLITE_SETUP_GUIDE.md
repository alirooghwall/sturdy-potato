# Satellite Imagery Analysis Setup Guide

Complete guide for setting up multi-source satellite imagery analysis with Sentinel-2, Google Earth Engine, MODIS, and temporal change detection.

## Overview

The ISR Platform now includes comprehensive satellite imagery analysis capabilities:

- **Multi-source data integration**: Sentinel-2, Google Earth Engine, MODIS, Landsat
- **Multi-temporal analysis**: Compare images across different dates
- **Change detection**: Deforestation, urban growth, flooding, wildfires
- **Agricultural monitoring**: Crop health, vegetation indices, irrigation
- **Long-term trend analysis**: Environmental changes over years
- **Real-time alerts**: Critical change detection with severity levels

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Sentinel-2 Setup (ESA Copernicus)](#sentinel-2-setup)
3. [Google Earth Engine Setup](#google-earth-engine-setup)
4. [MODIS Setup (NASA)](#modis-setup)
5. [Configuration](#configuration)
6. [API Usage](#api-usage)
7. [Analysis Types](#analysis-types)
8. [Best Practices](#best-practices)

---

## Prerequisites

### System Requirements

- Python 3.11+
- 8GB+ RAM (16GB recommended for large imagery)
- Storage: 100GB+ for imagery cache
- Internet connection for API access

### Install Dependencies

```bash
pip install earthengine-api sentinelsat rasterio geopandas opencv-python
```

Or using requirements.txt:

```bash
pip install -r requirements.txt
```

---

## Sentinel-2 Setup (ESA Copernicus)

### 1. Create Copernicus Account

1. Visit [Copernicus Open Access Hub](https://scihub.copernicus.eu/)
2. Click "Sign up" and create account
3. Verify email address
4. Login to confirm access

### 2. Get API Credentials

Your credentials are:
- **Username**: Your registered email or username
- **Password**: Your account password

### 3. Configure Environment

Add to `.env` file:

```bash
# Sentinel-2 (Copernicus)
SATELLITE_SENTINEL2_ENABLED=true
SATELLITE_SENTINEL2_USERNAME=your_username
SATELLITE_SENTINEL2_PASSWORD=your_password
SATELLITE_SENTINEL2_MAX_CLOUD_COVER=30
```

### 4. Define Areas of Interest

```python
# Example areas in Afghanistan
areas_of_interest = [
    {
        "name": "Kabul",
        "min_lon": 69.11, "min_lat": 34.47,
        "max_lon": 69.26, "max_lat": 34.62
    },
    {
        "name": "Kandahar",
        "min_lon": 65.65, "min_lat": 31.55,
        "max_lon": 65.83, "max_lat": 31.70
    }
]
```

### 5. Test Connection

```python
from src.services.connectors.sentinel2_connector import Sentinel2Connector
from src.services.satellite_analysis import BoundingBox

connector = Sentinel2Connector(
    username="your_username",
    password="your_password",
    areas_of_interest=[
        BoundingBox(69.11, 34.47, 69.26, 34.62)  # Kabul
    ]
)

# Test query
await connector.start()
products = await connector.fetch_data()
print(f"Found {len(products)} Sentinel-2 products")
```

### Sentinel-2 Features

- **Resolution**: 10m (visible/NIR), 20m (red edge/SWIR), 60m (coastal/cirrus)
- **Bands**: 13 spectral bands
- **Revisit time**: 5 days (with both satellites)
- **Coverage**: Global
- **Data format**: SAFE (Standard Archive Format for Europe)

---

## Google Earth Engine Setup

### 1. Create Google Cloud Project

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable Earth Engine API
4. Enable Cloud Storage API (for exports)

### 2. Register for Earth Engine

1. Visit [Google Earth Engine](https://earthengine.google.com/)
2. Sign up for access
3. Wait for approval (usually within 24 hours)

### 3. Create Service Account

```bash
# In Google Cloud Console
1. Go to IAM & Admin > Service Accounts
2. Create Service Account
3. Grant "Earth Engine Resource Writer" role
4. Create JSON key
5. Download key file
```

### 4. Configure Environment

Add to `.env`:

```bash
# Google Earth Engine
SATELLITE_GEE_ENABLED=true
SATELLITE_GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
SATELLITE_GEE_KEY_FILE=/path/to/service-account-key.json
```

### 5. Initialize Earth Engine

```python
import ee

# Authenticate
service_account = 'your-service-account@project.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, 'key-file.json')
ee.Initialize(credentials)

# Test
image = ee.Image('COPERNICUS/S2_SR/20230101T123456_20230101T123456_T42SWF')
print("Earth Engine initialized successfully")
```

### 6. Test Data Access

```python
from src.services.connectors.google_earth_engine import GoogleEarthEngineConnector
from src.services.satellite_analysis import BoundingBox

connector = GoogleEarthEngineConnector(
    service_account="your-account@project.iam.gserviceaccount.com",
    key_file="path/to/key.json",
    areas_of_interest=[
        BoundingBox(69.11, 34.47, 69.26, 34.62)
    ]
)

await connector.start()
data = await connector.fetch_data()
```

### Google Earth Engine Benefits

- Access to entire Landsat, Sentinel, MODIS archives
- Cloud-based processing (no local compute needed)
- Pre-processed datasets
- Time series analysis tools
- Free for research and education

---

## MODIS Setup (NASA)

### 1. Create NASA EarthData Account

1. Visit [NASA EarthData](https://urs.earthdata.nasa.gov/)
2. Register for account
3. Verify email
4. Approve applications that request data access

### 2. Get API Access (Optional)

For some products, you may need additional approval:

1. Go to [MODIS Web Service](https://modis.ornl.gov/)
2. Request API access
3. Note your credentials

### 3. Configure Environment

```bash
# MODIS
SATELLITE_MODIS_ENABLED=true
SATELLITE_MODIS_API_KEY=your_api_key  # Optional for some products
```

### 4. Test Connection

```python
from src.services.connectors.modis_connector import MODISConnector
from src.services.satellite_analysis import BoundingBox

connector = MODISConnector(
    api_key=None,  # Optional
    areas_of_interest=[
        BoundingBox(69.11, 34.47, 69.26, 34.62)
    ]
)

await connector.start()

# Get vegetation indices
vi_data = await connector.get_vegetation_indices(
    BoundingBox(69.11, 34.47, 69.26, 34.62),
    days_back=30
)

# Get fire detection
fires = await connector.get_fire_detection(
    BoundingBox(69.11, 34.47, 69.26, 34.62),
    days_back=7
)
```

### MODIS Products

- **MOD09**: Surface Reflectance (500m, 8-day)
- **MOD13**: Vegetation Indices (250m, 16-day)
- **MOD14**: Fire/Thermal Anomalies (1km, daily)
- **MOD11**: Land Surface Temperature (1km, daily)
- **MOD15**: LAI/FPAR (500m, 8-day)

---

## Configuration

### Complete Environment Configuration

```bash
# Satellite Imagery Configuration

# General Settings
SATELLITE_ENABLED=true
SATELLITE_CACHE_DIR=./data/satellite_cache
SATELLITE_MAX_CONCURRENT_DOWNLOADS=3

# Sentinel-2
SATELLITE_SENTINEL2_ENABLED=true
SATELLITE_SENTINEL2_USERNAME=your_username
SATELLITE_SENTINEL2_PASSWORD=your_password
SATELLITE_SENTINEL2_MAX_CLOUD_COVER=30

# Google Earth Engine
SATELLITE_GEE_ENABLED=true
SATELLITE_GEE_SERVICE_ACCOUNT=your-account@project.iam.gserviceaccount.com
SATELLITE_GEE_KEY_FILE=/path/to/key.json

# MODIS
SATELLITE_MODIS_ENABLED=true
SATELLITE_MODIS_API_KEY=optional_api_key

# Analysis Settings
SATELLITE_DEFORESTATION_THRESHOLD=0.2
SATELLITE_URBAN_GROWTH_THRESHOLD=0.15
SATELLITE_FLOOD_THRESHOLD=0.25
SATELLITE_FIRE_THRESHOLD=0.3

# Areas of Interest (JSON array)
SATELLITE_AOIS='[{"name":"Kabul","min_lon":69.11,"min_lat":34.47,"max_lon":69.26,"max_lat":34.62}]'
```

---

## API Usage

### Authentication

All satellite endpoints require authentication:

```bash
# Get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'

# Use token in requests
export TOKEN="your_jwt_token"
```

### List Available Images

```bash
curl -X GET "http://localhost:8000/api/v1/satellite/images?provider=SENTINEL_2&max_cloud_cover=20&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Deforestation Analysis

```bash
curl -X POST http://localhost:8000/api/v1/satellite/analysis/deforestation \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lon": 69.11,
      "min_lat": 34.47,
      "max_lon": 69.26,
      "max_lat": 34.62
    },
    "before_date": "2023-01-01T00:00:00Z",
    "after_date": "2024-01-01T00:00:00Z"
  }'
```

### Urban Growth Analysis

```bash
curl -X POST http://localhost:8000/api/v1/satellite/analysis/urban-growth \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lon": 69.11,
      "min_lat": 34.47,
      "max_lon": 69.26,
      "max_lat": 34.62
    },
    "before_date": "2020-01-01T00:00:00Z",
    "after_date": "2024-01-01T00:00:00Z"
  }'
```

### Flood Detection

```bash
curl -X POST http://localhost:8000/api/v1/satellite/analysis/flooding \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lon": 65.65,
      "min_lat": 31.55,
      "max_lon": 65.83,
      "max_lat": 31.70
    },
    "event_date": "2024-06-15T00:00:00Z",
    "baseline_date": "2024-06-01T00:00:00Z"
  }'
```

### Agriculture Monitoring

```bash
curl -X POST http://localhost:8000/api/v1/satellite/analysis/agriculture \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lon": 62.14,
      "min_lat": 34.28,
      "max_lon": 62.26,
      "max_lat": 34.40
    },
    "analysis_date": "2024-07-01T00:00:00Z"
  }'
```

### Wildfire Detection

```bash
curl -X POST http://localhost:8000/api/v1/satellite/analysis/wildfire \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lon": 64.0,
      "min_lat": 31.0,
      "max_lon": 65.0,
      "max_lat": 32.5
    },
    "detection_date": "2024-08-15T00:00:00Z",
    "pre_fire_date": "2024-08-01T00:00:00Z"
  }'
```

### Long-term Trend Analysis

```bash
curl -X POST http://localhost:8000/api/v1/satellite/analysis/long-term-trend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "DEFORESTATION",
    "bbox": {
      "min_lon": 69.5,
      "min_lat": 35.2,
      "max_lon": 70.0,
      "max_lat": 35.6
    },
    "start_date": "2020-01-01T00:00:00Z",
    "end_date": "2024-01-01T00:00:00Z"
  }'
```

---

## Analysis Types

### 1. Deforestation Detection

**Method**: NDVI (Normalized Difference Vegetation Index) comparison

**Formula**: NDVI = (NIR - Red) / (NIR + Red)

**Indicators**:
- NDVI decrease > 0.2 indicates forest loss
- Confidence based on magnitude of change

**Use Cases**:
- Illegal logging detection
- Agricultural expansion monitoring
- Forest fire damage assessment

### 2. Urban Growth Analysis

**Method**: NDBI (Normalized Difference Built-up Index)

**Formula**: NDBI = (SWIR - NIR) / (SWIR + NIR)

**Indicators**:
- NDBI increase > 0.15 indicates urbanization
- Annual growth rate calculation

**Use Cases**:
- Urban sprawl monitoring
- Infrastructure development tracking
- Population growth estimation

### 3. Flood Detection

**Method**: NDWI (Normalized Difference Water Index)

**Formula**: NDWI = (Green - NIR) / (Green + NIR)

**Indicators**:
- NDWI increase > 0.25 indicates flooding
- Severity levels: LOW, MEDIUM, HIGH, CRITICAL

**Use Cases**:
- Emergency response
- Flood extent mapping
- Damage assessment

### 4. Agriculture Monitoring

**Methods**: NDVI, NDWI, EVI (Enhanced Vegetation Index)

**Indicators**:
- Crop health index: 0-1 scale
- Vegetation vigor
- Irrigation detection

**Use Cases**:
- Crop health assessment
- Drought monitoring
- Yield prediction

### 5. Wildfire Detection

**Method**: NBR (Normalized Burn Ratio)

**Formula**: NBR = (NIR - SWIR) / (NIR + SWIR)

**Indicators**:
- dNBR (difference NBR) > 0.3 indicates burn
- Intensity: LOW, MEDIUM, HIGH, EXTREME

**Use Cases**:
- Active fire detection
- Burn severity assessment
- Recovery monitoring

### 6. Long-term Trends

**Method**: Time series analysis with linear regression

**Outputs**:
- Trend direction: INCREASING, DECREASING, STABLE, FLUCTUATING
- Rate of change per year
- Statistical significance (R²)
- Future predictions

**Use Cases**:
- Climate change impacts
- Environmental degradation
- Policy effectiveness evaluation

---

## Best Practices

### Image Selection

1. **Cloud Coverage**: Use images with <20% cloud cover for best results
2. **Season**: Compare images from same season to avoid phenological differences
3. **Time Gap**: Minimum 6 months between images for change detection
4. **Sensor Consistency**: Use same satellite/sensor for comparison when possible

### Analysis Tips

1. **Validation**: Always validate automated detections with ground truth
2. **Multiple Dates**: Use 3+ dates for trend analysis
3. **Buffer Zones**: Include buffer around AOI to avoid edge effects
4. **Atmospheric Correction**: Use Level-2A products (atmospherically corrected)

### Performance Optimization

1. **Cache**: Store processed imagery locally
2. **Parallel Processing**: Process multiple AOIs concurrently
3. **Cloud Computing**: Use Google Earth Engine for large-scale analysis
4. **Batch Processing**: Schedule analyses during off-peak hours

### Data Management

1. **Storage**: Plan for 1-10GB per Sentinel-2 scene
2. **Retention**: Keep analysis results for audit trail
3. **Backup**: Regular backups of critical analyses
4. **Documentation**: Document AOIs, dates, and analysis parameters

---

## Troubleshooting

### Sentinel-2 Issues

**Problem**: Authentication failed

**Solution**: 
- Verify username/password
- Check account is activated
- Ensure no IP restrictions

**Problem**: No products found

**Solution**:
- Check date range (data available from 2015+)
- Verify bounding box coordinates
- Increase cloud cover threshold

### Google Earth Engine Issues

**Problem**: Authentication error

**Solution**:
- Verify service account has Earth Engine access
- Check key file path and permissions
- Ensure Earth Engine API is enabled

**Problem**: Quota exceeded

**Solution**:
- Reduce concurrent requests
- Use smaller AOIs
- Implement rate limiting

### MODIS Issues

**Problem**: No data returned

**Solution**:
- MODIS has coarser resolution (250m-1km)
- Use larger AOIs (>25km x 25km)
- Check product availability dates

---

## Resources

### Documentation

- [Sentinel-2 User Guide](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi)
- [Google Earth Engine Guides](https://developers.google.com/earth-engine/guides)
- [MODIS Products](https://modis.gsfc.nasa.gov/data/dataprod/)

### Tools

- [QGIS](https://qgis.org/) - Desktop GIS for visualization
- [SNAP](https://step.esa.int/main/download/snap-download/) - ESA Sentinel Toolbox
- [Earth Engine Code Editor](https://code.earthengine.google.com/)

### Support

- Sentinel Hub: [support@sentinel-hub.com](mailto:support@sentinel-hub.com)
- Earth Engine: [Forum](https://groups.google.com/g/google-earth-engine-developers)
- MODIS: [Support](https://modis.gsfc.nasa.gov/about/contact.php)

---

**Last Updated**: January 2026  
**Version**: 2.0.0
