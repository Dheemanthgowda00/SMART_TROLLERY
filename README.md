# SMART_TROLLERY

**Smart Trolley Vision System** — an intelligent, Python-based project enabling autonomous trolley navigation and interaction using camera vision, QR code scanning, IR sensing, and human-following capabilities.

---

##  Table of Contents

- [Overview](#overview)  
- [Features](#features)  
- [Project Structure](#project-structure)  

---

## Overview

The **SMART_TROLLERY** system is designed to simulate or implement a smart shopping trolley capable of:

- Scanning and decoding QR codes for location or product identification.
- Following humans using vision-based algorithms.
- Integrating infrared (IR) logic for proximity sensing.
- Merging multiple data streams for refined navigation and behavior control.

Ideal for robotics enthusiasts, retail automation developers, or anyone exploring vision-driven systems for smart mobility!

---

## Features

- **QR Code Processing** (`QR_CODES/`)
  - Detects and interprets QR codes for dynamic positioning or action triggers.

- **Camera Indexing & Management** (`CAMERA_INDEX.py`)
  - Handles initialization and management of camera inputs and video streams.

- **Human-Following Logic** (`HUMAN_FOLLOWING.py`)
  - Implements algorithms for target detection and continuous tracking.

- **Infrared Sensor Handling** (`IR_LOGIC.py`)
  - Processes input from IR sensors to detect obstacles and measure proximity.

- **Core Behavior Integration** (`MERGED.py` / `FINAL.py`)
  - Fuses multiple sensory inputs to implement sophisticated control strategies.

- **QR Scanner Registry** (`QR_SCANNER_REGISTRY.py`)
  - Manages multiple QR scanning modules, enabling seamless integration.

---

## Project Structure

```
SMART_TROLLERY/
│
├── QR_CODES/ # QR-related assets or modules
├── templates/ # Storage for UI layouts or calibration files
├── CAMERA_INDEX.py # Camera setup and stream management
├── HUMAN_FOLLOWING.py # Vision-based person tracking
├── IR_LOGIC.py # Infrared obstacle detection
├── QR_SCANNER_REGISTRY.py # QR scanner coordination module
├── MERGED.py # Combined logic controller
└── FINAL.py # Polished final version of the system
```

