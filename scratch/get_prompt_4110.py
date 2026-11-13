import json

with open(r"C:\Users\soumy\.gemini\antigravity\brain\052b6941-8990-4a8d-a6bc-a50464cc197d\.system_generated\logs\transcript.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        step = item.get("step_index")
        if step and 4105 <= step <= 4120:
            print(f"STEP: {step} | source: {item.get('source')} | type: {item.get('type')}")
            c = item.get("content")
            if isinstance(c, str):
                print("CONTENT:", c[:300])
            elif isinstance(c, list):
                print("CONTENT LIST:", c)
            media = item.get("media")
            if media:
                print("MEDIA:", media)

