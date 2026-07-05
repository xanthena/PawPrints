from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
MAX_IMAGE_BYTES = int(float(os.getenv("VISION_MAX_IMAGE_MB", "20")) * 1024 * 1024)
