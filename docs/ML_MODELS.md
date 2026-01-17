# Afghanistan ISR Platform - AI/ML Model Specifications

## 1. Overview

This document specifies the AI/ML models used in the Afghanistan ISR Simulation & Analysis Platform. Each model is designed with military-grade requirements for accuracy, robustness, explainability, and operational reliability.

## 2. Model Catalog

| Model ID | Domain | Primary Task | Framework | Deployment |
|----------|--------|--------------|-----------|------------|
| VIS-001 | Visual | Object Detection | PyTorch | Triton |
| VIS-002 | Visual | Change Detection | PyTorch | Triton |
| VIS-003 | Visual | Flood Extent Mapping | PyTorch | Triton |
| NLP-001 | Text | Multilingual NER | Transformers | TensorFlow Serving |
| NLP-002 | Text | Topic Classification | Transformers | TensorFlow Serving |
| NLP-003 | Text | Sentiment Analysis | Transformers | TensorFlow Serving |
| NLP-004 | Text | Disinformation Detection | Transformers | TensorFlow Serving |
| NLP-005 | Text | Machine Translation | Transformers | TensorFlow Serving |
| GNN-001 | Graph | Network Analysis | PyTorch Geometric | Custom |
| GNN-002 | Graph | Influence Detection | PyTorch Geometric | Custom |
| TS-001 | Time-Series | Event Forecasting | PyTorch | TensorFlow Serving |
| TS-002 | Time-Series | Displacement Prediction | PyTorch | TensorFlow Serving |
| AD-001 | Anomaly | Geo-Movement Anomaly | Scikit-learn | Custom |
| AD-002 | Anomaly | Network Traffic Anomaly | PyTorch | Custom |
| AD-003 | Anomaly | Economic Indicators | Scikit-learn | Custom |
| FS-001 | Fusion | Multi-Sensor Track Fusion | Custom | C++ Native |
| TS-SCORE | Threat | Threat Scoring Ensemble | XGBoost + Rules | Custom |

---

## 3. Visual Models

### 3.1 VIS-001: Object Detection Model

**Purpose:** Detect and classify objects in satellite and UAV imagery including vehicles, personnel, encampments, weapons systems, and infrastructure.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VIS-001: Object Detection                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: RGB/Multispectral Image (1024x1024 tiles)               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    YOLOv8-X Backbone                        ││
│  │  ┌──────────────────────────────────────────────────────┐  ││
│  │  │ CSPDarknet53 + C2f Modules + SPPF                    │  ││
│  │  │ Input: 1024x1024x3 → Features: 32x32x1024            │  ││
│  │  └──────────────────────────────────────────────────────┘  ││
│  │                           │                                 ││
│  │                           ▼                                 ││
│  │  ┌──────────────────────────────────────────────────────┐  ││
│  │  │ PANet Feature Pyramid                                │  ││
│  │  │ Multi-scale features: P3, P4, P5                     │  ││
│  │  └──────────────────────────────────────────────────────┘  ││
│  │                           │                                 ││
│  │                           ▼                                 ││
│  │  ┌──────────────────────────────────────────────────────┐  ││
│  │  │ Detection Heads (Decoupled)                          │  ││
│  │  │ • Classification head: 23 classes                    │  ││
│  │  │ • Bounding box regression head                       │  ││
│  │  │ • Objectness score head                              │  ││
│  │  └──────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Output: List of detections with class, bbox, confidence        │
└─────────────────────────────────────────────────────────────────┘
```

#### Class Taxonomy

```yaml
classes:
  vehicles:
    - sedan
    - suv
    - pickup_truck
    - bus
    - truck_cargo
    - technical  # Armed vehicle
    - apc  # Armored Personnel Carrier
    - tank
    - motorcycle
  aircraft:
    - helicopter
    - fixed_wing_small
    - uav
  personnel:
    - individual
    - group_small  # 2-5
    - group_large  # 6+
  facilities:
    - building_residential
    - building_commercial
    - compound
    - checkpoint
    - encampment
  infrastructure:
    - bridge
    - road_damage
    - crater
```

#### Training Strategy

```yaml
training:
  base_model: yolov8x-coco-pretrained
  
  datasets:
    primary:
      - name: xView
        samples: 1_000_000
        classes: [vehicle, building, infrastructure]
      - name: DOTA
        samples: 188_000
        classes: [aircraft, vehicle, ship]
      - name: Custom-AFG
        samples: 50_000
        classes: [technical, encampment, checkpoint]
        source: Manually annotated Afghanistan imagery
        
    augmentation:
      geometric:
        - random_rotation: [-45, 45]
        - random_scale: [0.5, 2.0]
        - random_flip: horizontal
        - random_crop: True
      photometric:
        - brightness: [-0.2, 0.2]
        - contrast: [0.8, 1.2]
        - hue_saturation: True
        - noise_injection: gaussian
      domain_specific:
        - atmospheric_haze: True
        - shadow_augmentation: True
        - resolution_degradation: [0.3m, 5.0m]
        
  hyperparameters:
    optimizer: AdamW
    learning_rate: 0.001
    lr_schedule: cosine_annealing
    warmup_epochs: 3
    total_epochs: 100
    batch_size: 16
    weight_decay: 0.0005
    
  loss:
    classification: focal_loss
    bbox: ciou_loss
    objectness: bce_loss
    
  regularization:
    dropout: 0.1
    label_smoothing: 0.1
    mixup_alpha: 0.5
    mosaic_prob: 0.5

evaluation:
  metrics:
    - mAP@0.5
    - mAP@0.5:0.95
    - precision
    - recall
    - F1
  validation_split: 0.15
  test_split: 0.10
  
  performance_targets:
    mAP@0.5: >= 0.85
    mAP@0.5:0.95: >= 0.65
    inference_time_ms: <= 50  # Per 1024x1024 tile on V100
```

#### Few-Shot Adaptation

```yaml
few_shot:
  enabled: true
  method: prototypical_networks
  
  adaptation_protocol:
    support_set_size: [5, 10, 20]
    query_set_size: 15
    episodes_per_adaptation: 100
    
  use_cases:
    - new_vehicle_type
    - regional_building_style
    - seasonal_vegetation_change
    
  expected_performance:
    5_shot_accuracy: >= 0.70
    10_shot_accuracy: >= 0.80
    20_shot_accuracy: >= 0.85
```

### 3.2 VIS-002: Change Detection Model

**Purpose:** Detect changes between temporal satellite image pairs to identify new construction, damage, troop movements, etc.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VIS-002: Change Detection                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: Image Pair (T1, T2) - Registered, Same Region           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Siamese ResNet-50 Encoder                      ││
│  │                                                              ││
│  │  Image T1 ──┐                                                ││
│  │             ├──▶ Shared Weights ──▶ Features F1              ││
│  │  Image T2 ──┘                   ──▶ Features F2              ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Difference Module                               ││
│  │  • Absolute difference: |F1 - F2|                           ││
│  │  • Concatenation: [F1, F2]                                  ││
│  │  • Cross-attention: Attention(F1, F2)                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              UNet++ Decoder                                  ││
│  │  • Skip connections from encoder                            ││
│  │  • Dense skip pathways                                      ││
│  │  • Multi-scale output fusion                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  Output: Change Mask (semantic segmentation)                    │
│  Classes: no_change, construction, destruction, vehicle_appear, │
│           vehicle_disappear, vegetation_change, water_change    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 VIS-003: Flood Extent Mapping

**Purpose:** Segment flood extent from satellite imagery (optical and SAR) for disaster response.

```yaml
model:
  architecture: DeepLabV3+
  backbone: ResNet-101 (pretrained on ImageNet)
  
  input:
    optical: RGB + NIR (4 channels)
    sar: VV + VH polarization (2 channels)
    dem: Elevation data (1 channel)
    fusion: early_fusion  # Concatenate all inputs
    
  output:
    classes:
      - no_flood
      - flood_water
      - flood_vegetation  # Submerged vegetation
      - permanent_water
    resolution: 10m (matching Sentinel-2)
    
training:
  datasets:
    - Sen1Floods11
    - WorldFloods
    - Custom-AFG-Floods (2010-2024 events)
    
  augmentation:
    - random_crop
    - horizontal_flip
    - vertical_flip
    - random_rotation
    
  loss: 
    type: combined
    components:
      - dice_loss: 0.5
      - focal_loss: 0.5
      
  class_weights: [1.0, 2.0, 1.5, 0.5]  # Emphasize flood classes
  
evaluation:
  metrics:
    - IoU_per_class
    - mean_IoU
    - F1_flood_class
  target:
    mean_IoU: >= 0.75
    F1_flood: >= 0.85
```

---

## 4. NLP Models

### 4.1 NLP-001: Multilingual Named Entity Recognition

**Purpose:** Extract entities (persons, locations, organizations, events) from Dari, Pashto, Persian, Urdu, Arabic, and English text.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              NLP-001: Multilingual NER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: Raw text (any supported language)                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Language Detection                              ││
│  │  FastText language classifier → language_id                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              XLM-RoBERTa Large Encoder                       ││
│  │  • 550M parameters                                           ││
│  │  • 100 languages pretrained                                  ││
│  │  • Fine-tuned on multilingual NER                           ││
│  │  Input: Tokenized text (max 512 tokens)                     ││
│  │  Output: Contextual embeddings [batch, seq_len, 1024]       ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              CRF Layer                                       ││
│  │  Conditional Random Field for sequence labeling             ││
│  │  Enforces valid BIO tag sequences                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  Output: BIO-tagged entities                                    │
│  Labels: PER, LOC, ORG, GPE, EVENT, WEAPON, VEHICLE, FACILITY  │
└─────────────────────────────────────────────────────────────────┘
```

#### Training Data

```yaml
training_data:
  annotated_corpora:
    - WikiANN (40+ languages): 100K sentences
    - OntoNotes 5.0 (English, Arabic): 75K sentences
    - Custom Afghanistan corpus:
        dari: 15,000 sentences
        pashto: 12,000 sentences
        source: Annotated news, social media, reports
        annotation_guidelines: MUC-7 extended
        
  entity_types:
    - PERSON: Named individuals, titles
    - LOCATION: Geographic locations, landmarks
    - ORGANIZATION: Groups, agencies, companies
    - GPE: Geo-political entities (countries, provinces)
    - EVENT: Named events (operations, attacks, disasters)
    - WEAPON: Weapons, explosives, munitions
    - VEHICLE: Named vehicles, convoys
    - FACILITY: Buildings, bases, checkpoints
    - DATE: Dates, times, durations
    - MONEY: Monetary values
    
  data_augmentation:
    - entity_replacement: Replace entities with similar types
    - back_translation: Translate to English and back
    - mention_shuffling: Swap entity mentions
    
training:
  optimizer: AdamW
  learning_rate: 2e-5
  warmup_steps: 1000
  epochs: 10
  batch_size: 32
  gradient_accumulation: 4
  
  loss: crf_negative_log_likelihood
  
evaluation:
  metrics:
    - entity_F1 (strict)
    - entity_F1 (partial)
    - per_class_F1
    
  targets:
    overall_F1: >= 0.85
    dari_F1: >= 0.80
    pashto_F1: >= 0.78
```

### 4.2 NLP-004: Disinformation Detection

**Purpose:** Identify disinformation, propaganda, and coordinated inauthentic behavior in text content.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              NLP-004: Disinformation Detection                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: Text content + metadata                                 │
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │   Text Encoder       │  │   Metadata Encoder   │            │
│  │   (BLOOMZ-7B)        │  │   (MLP)              │            │
│  │                      │  │   • Source type      │            │
│  │   Text → [CLS]       │  │   • Account age      │            │
│  │   embedding          │  │   • Posting pattern  │            │
│  │   (4096-dim)         │  │   • Network features │            │
│  └──────────┬───────────┘  └──────────┬───────────┘            │
│             │                         │                         │
│             └────────────┬────────────┘                         │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Multi-Head Classifier                           ││
│  │                                                              ││
│  │  Head 1: Factual Accuracy                                   ││
│  │    → [Accurate, Misleading, False, Unverifiable]            ││
│  │                                                              ││
│  │  Head 2: Intent Classification                              ││
│  │    → [Informative, Opinion, Propaganda, Satire]             ││
│  │                                                              ││
│  │  Head 3: Coordination Signals                               ││
│  │    → [Organic, Possibly_Coordinated, Coordinated]           ││
│  │                                                              ││
│  │  Head 4: Overall Disinformation Score                       ││
│  │    → [0.0 - 1.0] continuous                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Explainability Layer                            ││
│  │  • Attention visualization                                  ││
│  │  • Key phrase extraction (what triggered classification)    ││
│  │  • Claim extraction for fact-checking                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Output:                                                        │
│  {                                                              │
│    "disinformation_score": 0.87,                               │
│    "factual_assessment": "FALSE",                              │
│    "intent": "PROPAGANDA",                                      │
│    "coordination": "COORDINATED",                              │
│    "key_phrases": ["eliminated all poverty", ...],             │
│    "claims": [{"claim": "...", "checkable": true}]             │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 NLP-005: Machine Translation

**Purpose:** Translate Dari, Pashto, and regional languages to English for analyst consumption.

```yaml
model:
  architecture: mBART-50
  size: large (610M parameters)
  
  supported_languages:
    tier_1:  # High quality
      - dari_to_english
      - pashto_to_english
      - persian_to_english
    tier_2:  # Good quality
      - urdu_to_english
      - arabic_to_english
    tier_3:  # Acceptable quality
      - tajik_to_english
      - uzbek_to_english
      
  fine_tuning:
    parallel_corpora:
      - OPUS-100 (multi-parallel)
      - UN Parallel Corpus
      - Custom Afghanistan corpus: 500K sentence pairs
      - Manual translations of Taliban statements
      
    domain_adaptation:
      - Military terminology glossary
      - Afghan place names gazetteer
      - Organization name dictionary
      
  decoding:
    method: beam_search
    beam_size: 5
    length_penalty: 1.0
    no_repeat_ngram: 3
    
evaluation:
  metrics:
    - BLEU
    - chrF++
    - Human evaluation (adequacy + fluency)
    
  targets:
    dari_to_english_BLEU: >= 35
    pashto_to_english_BLEU: >= 30
    human_adequacy: >= 4.0 / 5.0
```

---

## 5. Graph Neural Network Models

### 5.1 GNN-001: Network Analysis

**Purpose:** Analyze social and organizational networks to identify communities, key actors, and hidden relationships.

```
┌─────────────────────────────────────────────────────────────────┐
│              GNN-001: Network Analysis                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: Heterogeneous graph                                     │
│    Node types: Person, Organization, Location, Event, Account   │
│    Edge types: knows, member_of, located_at, participated_in    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Node Feature Encoder                            ││
│  │  Person: [text_embedding, activity_features]                ││
│  │  Organization: [text_embedding, size, type]                 ││
│  │  Location: [coordinates, type, population]                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Heterogeneous Graph Transformer (HGT)           ││
│  │  • 4 layers                                                 ││
│  │  • 8 attention heads                                        ││
│  │  • Hidden dim: 256                                          ││
│  │  • Edge-type aware attention                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Task-Specific Heads                             ││
│  │                                                              ││
│  │  Community Detection:                                        ││
│  │    → Soft clustering assignment                             ││
│  │                                                              ││
│  │  Link Prediction:                                            ││
│  │    → Probability of hidden/future edges                     ││
│  │                                                              ││
│  │  Node Classification:                                        ││
│  │    → Role classification (leader, financier, operative)     ││
│  │                                                              ││
│  │  Influence Scoring:                                          ││
│  │    → Centrality and influence measures                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Output:                                                        │
│  {                                                              │
│    "communities": [{id, members, cohesion}],                   │
│    "key_actors": [{node_id, influence_score, role}],           │
│    "predicted_links": [{source, target, probability}],         │
│    "anomalous_structures": [{subgraph, anomaly_score}]         │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Time-Series Models

### 6.1 TS-001: Event Forecasting

**Purpose:** Predict likelihood and characteristics of future security events based on historical patterns.

```yaml
model:
  architecture: Temporal Fusion Transformer (TFT)
  
  input_features:
    static:  # Per location
      - population_density
      - terrain_type
      - distance_to_border
      - historical_incident_rate
      
    time_varying_known:  # Future known
      - day_of_week
      - month
      - islamic_calendar_events
      - seasonal_factors
      - weather_forecast
      
    time_varying_observed:  # Historical only
      - recent_incident_count
      - recent_sigint_activity
      - recent_population_movement
      - social_media_sentiment
      - economic_indicators
      
  output:
    horizon: 7 days
    quantiles: [0.1, 0.25, 0.5, 0.75, 0.9]
    predictions:
      - incident_count (per district)
      - incident_type_distribution
      - severity_distribution
      
  architecture_details:
    hidden_size: 256
    attention_heads: 8
    lstm_layers: 2
    dropout: 0.1
    
training:
  loss: quantile_loss
  optimizer: Adam
  learning_rate: 0.001
  epochs: 100
  early_stopping: patience=10
  
evaluation:
  metrics:
    - MAE
    - RMSE
    - Quantile Loss
    - Calibration (coverage of prediction intervals)
    
  targets:
    MAE: <= 2.0 incidents/week/district
    90%_interval_coverage: >= 0.85
```

### 6.2 TS-002: Population Displacement Prediction

**Purpose:** Forecast population displacement trajectories for humanitarian planning.

```yaml
model:
  architecture: Seq2Seq with Attention (LSTM-based)
  
  input:
    historical_displacement_data:
      source: UNHCR, IOM, local registrations
      granularity: weekly, district-level
      
    contextual_features:
      - conflict_intensity (from TS-001)
      - natural_disaster_indicators
      - economic_conditions
      - seasonal_patterns
      - route_accessibility
      
  output:
    horizon: 12 weeks
    predictions:
      - displacement_volume_per_origin
      - destination_distribution
      - route_usage_probability
      
training:
  data:
    historical_period: 2010-2025
    train_test_split: temporal (2023 cutoff)
    
  loss: MSE + KL_divergence (for distribution)
  
evaluation:
  metrics:
    - Volume prediction MAPE
    - Destination distribution accuracy
    - Early warning lead time
```

---

## 7. Anomaly Detection Models

### 7.1 AD-001: Geo-Movement Anomaly Detection

```yaml
model:
  name: AD-001
  type: Ensemble
  
  components:
    isolation_forest:
      purpose: Detect point anomalies
      features:
        - vehicle_count
        - time_of_day
        - day_of_week
        - route_segment
      contamination: 0.05
      
    lstm_autoencoder:
      purpose: Detect sequence anomalies
      input: Time-series of movement patterns
      architecture:
        encoder_lstm: [128, 64]
        latent_dim: 32
        decoder_lstm: [64, 128]
      threshold: reconstruction_error > 3*std
      
    statistical_baseline:
      purpose: Detect deviation from historical norms
      method: Z-score against rolling 30-day baseline
      threshold: |z| > 3.0
      
  ensemble_method:
    type: weighted_voting
    weights:
      isolation_forest: 0.3
      lstm_autoencoder: 0.4
      statistical: 0.3
    final_threshold: 0.6
    
  training:
    data:
      source: Historical vehicle movement data
      period: 2020-2025
      normal_period: Labeled "normal" operations
      
    validation:
      known_anomalies: 500 labeled events
      target_detection_rate: >= 0.90
      target_false_positive_rate: <= 0.05
```

### 7.2 AD-002: Network Traffic Anomaly Detection

```yaml
model:
  name: AD-002
  type: DeepLog variant
  
  architecture:
    input: Sequence of network log events (tokenized)
    model: Transformer Encoder
    layers: 4
    heads: 8
    hidden_dim: 256
    
  training:
    method: Self-supervised (next event prediction)
    data: Normal network traffic logs
    
  inference:
    method: Anomaly if predicted probability < threshold
    threshold: Dynamically adjusted per context
    
  outputs:
    - anomaly_score: 0-1
    - anomalous_events: List of unusual log entries
    - potential_attack_type: Classification suggestion
```

---

## 8. Sensor Fusion Model

### 8.1 FS-001: Multi-Sensor Track Fusion

```
┌─────────────────────────────────────────────────────────────────┐
│              FS-001: Multi-Sensor Track Fusion                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input Sources:                                                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │
│  │ Satellite │ │ UAV EO/IR │ │ Radar     │ │ SIGINT    │       │
│  │ Imagery   │ │           │ │           │ │           │       │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘       │
│        │             │             │             │              │
│        └─────────────┴─────────────┴─────────────┘              │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Track Association                               ││
│  │  • Global Nearest Neighbor (GNN)                            ││
│  │  • Joint Probabilistic Data Association (JPDA)              ││
│  │  • Multiple Hypothesis Tracking (MHT)                       ││
│  │                                                              ││
│  │  Distance metrics:                                          ││
│  │  • Mahalanobis distance (spatial)                           ││
│  │  • Temporal proximity                                        ││
│  │  • Feature similarity (if available)                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              State Estimation                                ││
│  │                                                              ││
│  │  Extended Kalman Filter (EKF):                              ││
│  │  • State: [x, y, z, vx, vy, vz]                             ││
│  │  • Process model: Constant velocity + noise                 ││
│  │  • Measurement models: Per sensor type                      ││
│  │                                                              ││
│  │  Interacting Multiple Model (IMM):                          ││
│  │  • Models: Constant velocity, Constant acceleration, Turn   ││
│  │  • Adaptive model switching                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Track Management                                ││
│  │  • Track initiation (M-of-N logic)                          ││
│  │  • Track confirmation                                        ││
│  │  • Track deletion (coast timeout)                           ││
│  │  • Track merging (duplicate elimination)                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Output: Fused tracks with confidence, covariance, attribution  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Threat Scoring Model

### 9.1 TS-SCORE: Threat Scoring Ensemble

```yaml
model:
  name: TS-SCORE
  type: Ensemble (XGBoost + Rule Engine)
  
  components:
    ml_model:
      algorithm: XGBoost
      objective: regression (score 0-100)
      
      features:
        credibility:
          - source_reliability_score
          - number_of_corroborating_sources
          - recency_of_information
          - historical_source_accuracy
          
        tactical_impact:
          - proximity_to_population_center_km
          - proximity_to_critical_infrastructure_km
          - civilian_density_in_area
          - military_assets_at_risk
          
        capability:
          - estimated_group_size
          - known_weapons_capability
          - historical_attack_sophistication
          - financial_resources_indicator
          
        vulnerability:
          - target_security_posture
          - terrain_defensibility
          - response_force_proximity
          - civilian_vulnerability_index
          
        time_sensitivity:
          - intelligence_age_hours
          - chatter_intensity_trend
          - event_imminence_indicators
          
      training:
        data: Historical threat assessments with analyst scores
        samples: 50,000 labeled cases
        cross_validation: 5-fold stratified
        
    rule_engine:
      rules:
        - IF known_hvt_involved THEN score += 20
        - IF imminent_attack_signal AND high_confidence THEN score += 30
        - IF mass_casualty_potential THEN score *= 1.3
        - IF verified_by_multiple_int THEN confidence += 0.2
        
  ensemble_method:
    ml_weight: 0.7
    rules_weight: 0.3
    final_score: weighted_sum
    
  explainability:
    method: SHAP (TreeExplainer)
    outputs:
      - feature_importance_global
      - feature_contribution_local
      - natural_language_summary
      
  thresholds:
    LOW: [0, 30]
    MEDIUM: [31, 60]
    HIGH: [61, 85]
    CRITICAL: [86, 100]
```

---

## 10. Model Deployment & Operations

### 10.1 Model Serving Infrastructure

```yaml
serving_infrastructure:
  platforms:
    triton_inference_server:
      models: [VIS-001, VIS-002, VIS-003]
      hardware: NVIDIA A100 GPUs
      batching:
        max_batch_size: 32
        max_queue_delay_ms: 100
      scaling:
        min_replicas: 2
        max_replicas: 10
        target_gpu_utilization: 0.7
        
    tensorflow_serving:
      models: [NLP-001, NLP-002, NLP-003, NLP-004, NLP-005]
      hardware: CPU or GPU (configurable)
      batching:
        max_batch_size: 64
        batch_timeout_ms: 50
      scaling:
        min_replicas: 3
        max_replicas: 20
        target_cpu_utilization: 0.6
        
    custom_serving:
      models: [GNN-001, GNN-002, AD-001, AD-002, FS-001, TS-SCORE]
      framework: FastAPI + Ray Serve
      hardware: CPU (graph models), GPU (anomaly detection)
```

### 10.2 Model Monitoring

```yaml
monitoring:
  metrics:
    performance:
      - latency_p50, latency_p95, latency_p99
      - throughput_rps
      - error_rate
      - batch_utilization
      
    data_quality:
      - input_drift (KS statistic vs training distribution)
      - missing_features_rate
      - out_of_vocabulary_rate (NLP)
      
    model_quality:
      - prediction_confidence_distribution
      - output_drift
      - feature_importance_stability
      
  alerting:
    latency_p99 > 500ms: WARN
    error_rate > 1%: CRITICAL
    input_drift_ks > 0.1: WARN
    prediction_confidence < 0.5 (sustained): WARN
    
  retraining_triggers:
    - accuracy_degradation > 5%
    - significant_data_drift (p < 0.01)
    - scheduled: quarterly
    - manual: analyst request
```

### 10.3 Model Versioning & Registry

```yaml
model_registry:
  platform: MLflow
  
  metadata_tracked:
    - model_id
    - version
    - training_date
    - training_data_hash
    - hyperparameters
    - evaluation_metrics
    - deployment_status
    
  lifecycle_stages:
    - Development
    - Staging
    - Production
    - Archived
    
  approval_workflow:
    staging_to_production:
      - Automated tests pass
      - Performance benchmarks met
      - Security review complete
      - Analyst acceptance testing
      - Change advisory board approval
```

---

## 11. Explainability Framework

### 11.1 XAI Methods by Model Type

```yaml
explainability:
  visual_models:
    methods:
      - GradCAM: Highlight image regions driving predictions
      - Saliency_maps: Gradient-based importance
      - Bounding_box_overlay: Show detected objects
    output: Image with overlays + JSON feature importance
    
  nlp_models:
    methods:
      - Attention_visualization: Transformer attention weights
      - LIME: Local surrogate explanations
      - Key_phrase_extraction: Phrases driving classification
    output: Highlighted text + importance scores
    
  tabular_models:
    methods:
      - SHAP: TreeExplainer for XGBoost
      - Feature_importance: Global and local
      - Counterfactual: "What would change the prediction?"
    output: Feature contribution chart + natural language summary
    
  graph_models:
    methods:
      - Subgraph_highlighting: Important nodes and edges
      - Attention_weights: GNN attention interpretation
      - Path_explanation: Important paths in network
    output: Subgraph visualization + importance scores
```

### 11.2 Natural Language Explanation Generation

```yaml
nl_explanation:
  model: Fine-tuned T5
  
  input:
    - prediction_type
    - prediction_value
    - feature_importances
    - key_evidence
    
  output_template:
    threat_score: |
      "The threat score of {score} ({category}) was primarily driven by:
      {top_factors_list}. The score {trend_description} over the past
      {time_period} due to {change_reasons}."
      
    disinformation: |
      "This content was classified as {verdict} with {confidence}% confidence.
      Key indicators include: {indicators_list}. The claim '{main_claim}'
      contradicts verified information from {sources}."
```

---

## 12. Bias & Fairness Considerations

### 12.1 Bias Mitigation

```yaml
bias_mitigation:
  geographic_bias:
    issue: Models may perform differently across regions
    mitigation:
      - Stratified sampling by province during training
      - Regional performance monitoring
      - Fine-tuning on underrepresented regions
      
  temporal_bias:
    issue: Older patterns may not reflect current reality
    mitigation:
      - Rolling training windows
      - Decay weighting for older samples
      - Regular retraining schedule
      
  source_bias:
    issue: Some sources may be over/under-represented
    mitigation:
      - Source balancing during training
      - Credibility weighting
      - Multi-source corroboration requirements
      
  language_bias:
    issue: Dominant languages may have better performance
    mitigation:
      - Language-stratified evaluation
      - Additional fine-tuning for low-resource languages
      - Performance parity targets
```

### 12.2 Fairness Monitoring

```yaml
fairness_monitoring:
  dimensions:
    - geographic_region
    - language
    - source_type
    - entity_type
    
  metrics:
    - equalized_odds
    - demographic_parity
    - calibration_by_group
    
  thresholds:
    max_performance_gap: 10%  # Between best and worst group
    
  reporting:
    frequency: monthly
    recipients: model governance board
```

---

## 13. Security Considerations

### 13.1 Model Security

```yaml
model_security:
  adversarial_robustness:
    testing:
      - FGSM attacks on visual models
      - TextFooler attacks on NLP models
      - Membership inference attacks
    defense:
      - Adversarial training
      - Input validation and sanitization
      - Ensemble diversity
      
  model_confidentiality:
    - Models stored in encrypted storage
    - Model weights not exposed via API
    - No raw model download endpoints
    
  input_validation:
    - Schema validation
    - Size limits
    - Content type verification
    - Malicious payload detection
```

---

*Document Version: 1.0*  
*Classification: UNCLASSIFIED // FOR OFFICIAL USE ONLY*  
*Last Updated: 2026-01-17*
