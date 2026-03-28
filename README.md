# MARSPACE - National Critical Infrastructure Protection Command Center

MARSPACE is an autonomous crisis management dashboard designed for space weather events (solar storms) that threaten terrestrial infrastructure.

## Key Features
- **SCADA Decision Engine**: AI-powered crisis analysis using local LLMs (Gemma-4B).
- **L1 DSCOVR Telemetry**: Real-time monitoring of Solar Wind, GIC, Kp Index, and Bz Magnetic Field.
- **Air-Gapped Solar Monitoring**: On-device sunspot detection using YOLOv11 (completely offline).
- **Interactive Crisis Map**: Dynamic visualization of metro networks, energy grids, and resilient AREDN mesh communication nodes.

## Backend Components
- `proxy.py`: Central data hub and CORS-enabled API proxy.
- `stream_loop.py`: Real-time solar imagery server with local AI inference.
- `simulate_sensor.py`: High-fidelity telemetry simulator for DSCOVR sensor data.

## Vision: Operational Resilience
Designed for absolute autonomy. In the event of a total internet blackout during a G5-class solar storm, MARSPACE continues to function using local AI engines and terrestrial mesh networks.

---
*Developed for the TUA Astro Hackathon.*
