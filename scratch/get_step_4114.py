import json

with open(r"C:\Users\soumy\.gemini\antigravity\brain\052b6941-8990-4a8d-a6bc-a50464cc197d\.system_generated\logs\transcript_full.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        if item.get("step_index") == 4114:
            print("STEP 4114 CONTENT:")
            print(item.get("content"))

