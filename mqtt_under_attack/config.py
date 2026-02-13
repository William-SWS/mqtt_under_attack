from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

# Base data directory (can be overridden via .env)
_default_data_dir = PROJ_ROOT / "data"
DATA_DIR = Path(getenv("DATA_DIR", str(_default_data_dir)))
logger.info(f"DATA_DIR path is: {DATA_DIR}")

RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# Models directory (can be overridden via .env)
_default_models_dir = PROJ_ROOT / "models"
MODELS_DIR = Path(getenv("MODELS_DIR", str(_default_models_dir)))
logger.info(f"MODELS_DIR path is: {MODELS_DIR}")

# Reports directory (can be overridden via .env)
_default_reports_dir = PROJ_ROOT / "reports"
REPORTS_DIR = Path(getenv("REPORTS_DIR", str(_default_reports_dir)))
logger.info(f"REPORTS_DIR path is: {REPORTS_DIR}")

# Figures directory (can be overridden via .env)
# By default, it's inside REPORTS_DIR, but can be set independently
_default_figures_dir = REPORTS_DIR / "figures"
FIGURES_DIR = Path(getenv("FIGURES_DIR", str(_default_figures_dir)))
logger.info(f"FIGURES_DIR path is: {FIGURES_DIR}")

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
