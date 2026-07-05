from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# "api_key" (default): Gemini Developer API / AI Studio, the main path --
#   what judges/teammates use, needs only GEMINI_API_KEY.
# "vertex": Vertex AI + Application Default Credentials, needs
#   GOOGLE_PROJECT_ID and `gcloud auth application-default login` --
#   for testing against a GCP account's free credits when the AI Studio
#   free tier itself won't allow calls.
GEMINI_AUTH_MODE = os.getenv("GEMINI_AUTH_MODE", "api_key").strip().lower()
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# lets the same local adapter point at any vision-capable model Ollama
# is serving, not just qwen2.5vl:3b
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")

MAX_IMAGE_BYTES = int(float(os.getenv("VISION_MAX_IMAGE_MB", "20")) * 1024 * 1024)
