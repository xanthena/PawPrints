from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = REPO_ROOT / "src" / "data"
JSONS_DIR = DATA_DIR / "jsons"
OUTPUT_DIR = REPO_ROOT / "src" / "results" / "highlight-reel"
