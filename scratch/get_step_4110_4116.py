import json

with open(r"C:\Users\soumy\.gemini\antigravity\brain\052b6941-8990-4a8d-a6bc-a50464cc197d\.system_generated\logs\transcript_full.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        step = item.get("step_index")
        if step and 4110 <= step <= 4116:
            c = item.get("content")
            if c:
                print(f"STEP {step} (type {item.get('type')}):")
                print(str(c)[:500])

