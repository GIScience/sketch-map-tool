# Model Registry for SketchMapTool

## Overview
The **Model Registry** maintains a collection of fine-tuned machine learning models specifically developed for the **SketchMapTool** project. These models are designed to handle different tasks, including **object detection**, **image classification**, and **segmentation**.


## Model Usage
| Task                 | Model Name | Modification    |Purpose | URL Link                                                           |
|----------------------|------------|-----------------|---------|--------------------------------------------------------------------|
| Object Detection     | YOLO_OSM   | 6-Channel Input |Detects sketches on OSM | [download](https://sketch-map-tool.heigit.org/weights/SMT-OSM.pt)  |
| Object Detection     | YOLO_ESRI  | 6-Channel Input | Detects sketches on ESRI maps | [download](https://sketch-map-tool.heigit.org/weights/SMT-ESRI.pt) |
| Image Classification | YOLO_CLS   | tandard RGB     |Classifies colors in sketches | [download](https://sketch-map-tool.heigit.org/weights/SMT-CLS.pt)  |
| Segmentation         | SAM2       | tandard RGB     | Performs segmentation on sketch | [github](https://github.com/facebookresearch/sam2)                 |

## Models in the Registry
### 1. Object Detection Models
Two separate object detection models have been trained for each based map: **OSM** and **ESRI**. These models detect key objects from sketches drawn on different base maps.
To effectively detect sketches and distinguish them from base map elements, we have **modified the YOLO model architecture** to process **6-channel inputs instead of the standard 3-channel RGB**. 
This approach combines the **reference base map (3-channel RGB)** and the **map with overlaid sketches (3-channel RGB)** into a **single 6-channel image**, allowing the model to jointly learn features from both layers. 
This architectural change enhances the model’s ability to differentiate sketches from existing map features, leading to improved detection accuracy.

#### **OSM Object Detection Model**
- **Base Map:** OpenStreetMap (OSM)
- **Task:** Identifies and differentiates sketches from existing OSM features.
- **Fine-tuned On:** Custom-labeled OSM dataset with annotated sketches.

#### **ESRI Object Detection Model**
- **Base Map:** ESRI Satellite Imagery
- **Task:** Detects and isolates sketches overlaid on satellite ESRI imagery.
- **Fine-tuned On:** Custom dataset with labeled sketches on ESRI base maps.

### 2. Image Classification Model
This model is used to determine the sketch's **color**.

#### **Sketch Color Classification Model**
- **Task:** Classifies colors of drawn strokes to differentiate map elements.
- **Fine-tuned On:** Custom dataset with labeled sketch color samples.

### 3. Segmentation Model
For segmentation tasks, **SAM2 (Segment Anything Model v2)** is utilized.

#### **SAM2 - Segmentation Model**
- **Task:** Performs pixel-wise segmentation to extract regions from sketches.


For questions, contact the **SketchMapTool Team**.

