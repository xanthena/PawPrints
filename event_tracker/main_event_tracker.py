from timeline_exporter import generate_timeline

INPUT_JSON = r"PawPrints/jsons/qwen.json"

OUTPUT_JSON = r"PawPrints/jsons/timeline_qwen.json"


timeline = generate_timeline(

    input_file=INPUT_JSON,

    output_file=OUTPUT_JSON

)

print(f"Frames in timeline: {len(timeline)}")