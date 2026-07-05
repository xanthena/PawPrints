import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
JSONS_DIR = REPO_ROOT / "src" / "data" / "jsons"

if __package__ in (None, ""):
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.event_builder.event_pipeline import run_event_pipeline
else:
    from .event_pipeline import run_event_pipeline

INPUT_MODE = "local"
INPUT_OPTIONS = {
    "local": JSONS_DIR / "qwen.json",
    "cloud": JSONS_DIR / "gemini.json",
}
OUTPUT_OPTIONS = {
    "local": JSONS_DIR / "final_timeline_qwen.json",
    "cloud": JSONS_DIR / "final_timeline_gemini.json",
}


def get_input_json(input_mode):
    try:
        return INPUT_OPTIONS[input_mode]
    except KeyError as error:
        valid_modes = ", ".join(sorted(INPUT_OPTIONS))
        raise ValueError(
            f"Unknown input mode '{input_mode}'. Use one of: {valid_modes}."
        ) from error


def get_output_json(input_mode):
    try:
        return OUTPUT_OPTIONS[input_mode]
    except KeyError as error:
        valid_modes = ", ".join(sorted(OUTPUT_OPTIONS))
        raise ValueError(
            f"Unknown output mode '{input_mode}'. Use one of: {valid_modes}."
        ) from error


def main():
    input_json = get_input_json(INPUT_MODE)
    output_json = get_output_json(INPUT_MODE)
    final_events = run_event_pipeline(input_json, output_json)
    print(f"Input mode: {INPUT_MODE}")
    print(f"Input JSON: {input_json}")
    print(f"Generated {len(final_events)} events")
    print(output_json)


if __name__ == "__main__":
    main()


