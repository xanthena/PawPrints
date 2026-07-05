from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAX_IMAGE_BYTES = int(float(os.getenv("VISION_MAX_IMAGE_MB", "20")) * 1024 * 1024)
