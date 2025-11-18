import argparse
import logging
import subprocess
import sys
from pathlib import Path

from modules.data_pipeline.global_dataset_loader import DEFAULT_DATASET_PATH

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("auto_retrain_global")

BASE_DIR = Path(__file__).resolve().parents[1]

COMMANDS = [
    ["python", "scripts/train_rl_inventory.py", "--data", str(DEFAULT_DATASET_PATH), "--global_mode"],
    ["python", "scripts/train_forecast.py", "--data", str(DEFAULT_DATASET_PATH), "--global_mode"],
    ["python", "scripts/train_late_delivery.py", "--data", str(DEFAULT_DATASET_PATH)],
    ["python", "scripts/train_pricing_elasticity.py", "--data", str(DEFAULT_DATASET_PATH)],
]

def run_command(cmd):
    logger.info("Running: %s", " ".join(cmd))
    process = subprocess.run(cmd, cwd=BASE_DIR)
    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")

def main():
    for cmd in COMMANDS:
        run_command(cmd)
    logger.info("Auto retrain pipeline completed.")

if __name__ == "__main__":
    main()
