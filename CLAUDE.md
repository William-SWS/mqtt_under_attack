# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a machine learning pipeline for detecting DoS (Denial of Service) attacks in MQTT networks. The project implements a complete ML pipeline with data preprocessing, feature engineering, model training with Optuna optimization, and evaluation. It includes deployment guides for edge computing on Raspberry Pi.

## Common Commands

### Running the Complete Pipeline
```bash
python main.py
```
This orchestrates the entire pipeline: data loading → training → evaluation for all ML algorithms.

### Development Commands
```bash
make requirements      # Install Python dependencies
make format           # Format code with ruff
make lint             # Lint code with ruff
make data             # Generate dataset (if needed)
```

### Running Individual Scripts
```bash
python scripts/data_loader.py    # Load and preprocess data
python scripts/train.py          # Train models with Optuna optimization
python scripts/evaluate.py       # Evaluate trained models
```

### Working with Notebooks
The refactored notebooks in `notebooks_refactored/` contain the complete pipeline implementations:
- `01_dos_complete_pipeline.ipynb` - Original baseline with global fillna(0)
- `02_dos_complete_pipeline.ipynb` - Constant imputation (SimpleImputer with fill_value=0)
- `03_dos_complete_pipeline.ipynb` - Median imputation (SimpleImputer with strategy='median')

## Architecture

### Pipeline Structure
The ML pipeline follows a linear, unidirectional flow:

1. **Data Loading** (`scripts/data_loader.py`)
   - Loads raw MQTT traffic data from `data/raw/`
   - Calculates gap features and performs data cleaning
   - Splits and scales data for training

2. **Model Training** (`scripts/train.py`)
   - Implements Optuna hyperparameter optimization
   - Trains multiple ML algorithms in parallel
   - Saves optimized models to `models_optimized/`

3. **Evaluation** (`scripts/evaluate.py`)
   - Generates performance metrics and confusion matrices
   - Creates comprehensive reports
   - Validates model inference

### Key ML Algorithms
The pipeline optimizes and evaluates these algorithms:
- RandomForest
- DecisionTree
- GaussianNB
- LDA (Linear Discriminant Analysis)
- QDA (Quadratic Discriminant Analysis)
- GradientBoosting

### Package Structure
- `mqtt_under_attack/` - Main package with core modules
  - `dataset.py` - Data loading utilities
  - `features.py` - Feature engineering
  - `modeling/train.py` - Model training logic
  - `modeling/predict.py` - Model inference
  - `plots.py` - Visualization utilities
  - `config.py` - Configuration variables

### Data Flow
Raw data → `data/raw/` → Processed features → Trained models → `models_optimized/` → Evaluation reports → `reports_refactored/`

## Important Notes

### Missing Value Strategies
The project evaluates three approaches for handling missing values:
1. **Baseline**: Global `fillna(0)` before train_test_split (has design leakage)
2. **Constant**: `SimpleImputer(strategy='constant', fill_value=0)` post-split (recommended)
3. **Median**: `SimpleImputer(strategy='median')` post-split (causes performance degradation)

### Deployment
The project includes deployment guides for Raspberry Pi edge computing in `raspberry_deploy.md`. Models are optimized for low-resource environments.

### Performance Characteristics
- DecisionTree consistently achieves highest F1-scores (~0.975)
- Linear/probabilistic models (LDA, QDA) are sensitive to imputation strategy
- Median imputation causes significant performance drop for discriminant models

## Development Workflow

When modifying the pipeline:
1. Test changes in notebooks first (`notebooks_refactored/`)
2. Update corresponding scripts in `scripts/` if changes are validated
3. Run `python main.py` to execute the complete pipeline
4. Review results in `reports_refactored/` directory

The `main.py` orchestrator ensures scripts run in the correct order and handles data flow between stages.