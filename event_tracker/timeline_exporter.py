"""
Loads benchmark JSON, builds a timeline and saves it.
"""

import json

from timeline_builder import build_timeline


def generate_timeline(input_file, output_file):

    with open(input_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    timeline = build_timeline(results)

    with open(output_file, "w", encoding="utf-8") as f:

        json.dump(
            timeline,
            f,
            indent=4,
            ensure_ascii=False
        )

    print("=" * 80)
    print("Timeline Generated")
    print(output_file)
    print("=" * 80)

    return timeline