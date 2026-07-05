from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = REPO_ROOT / "src" / "data"
JSONS_DIR = DATA_DIR / "jsons"
SOURCE_VIDEO = DATA_DIR / "source_video" / "full-cat-video.mp4"
OUTPUT_DIR = REPO_ROOT / "src" / "results" / "highlight-reel"
