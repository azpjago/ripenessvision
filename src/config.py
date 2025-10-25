import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
AUGMENTED_DATA_DIR = DATA_DIR / 'augmented'

# Model directories
MODELS_DIR = BASE_DIR / 'models'
TRAINED_MODELS_DIR = MODELS_DIR / 'trained_models'
SAVED_WEIGHTS_DIR = MODELS_DIR / 'saved_weights'

# Results directories
RESULTS_DIR = BASE_DIR / 'results'
FIGURES_DIR = RESULTS_DIR / 'figures'
METRICS_DIR = RESULTS_DIR / 'metrics'
PREDICTIONS_DIR = RESULTS_DIR / 'predictions'

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, AUGMENTED_DATA_DIR,
                  TRAINED_MODELS_DIR, SAVED_WEIGHTS_DIR,
                  FIGURES_DIR, METRICS_DIR, PREDICTIONS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Model configuration
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 50
NUM_CLASSES = 9  # 3 fruits × 3 ripeness levels

# Classes
FRUITS = ['tomato', 'mango', 'banana']
RIPENESS_LEVELS = ['unripe', 'ripe', 'overripe']
CLASSES = [f"{fruit}_{ripeness}" for fruit in FRUITS for ripeness in RIPENESS_LEVELS]