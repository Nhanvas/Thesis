# PyTorch Project Template

A starter template for ML projects.

## Structure

    src/
    ├── configs/          # YAML config files
    ├── logs/             # Training logs
    ├── shared/
    │   ├── helper/       # Utility functions
    │   ├── models/       # Model definitions
    │   └── services/     # Data loading, training logic
    ├── inference_pipeline.py
    ├── train_pipeline.py
    └── test_pipeline.py

## Setup

    pip install -r requirements.txt

## Usage

    python src/train_pipeline.py
    python src/test_pipeline.py
    python src/inference_pipeline.py
