import json

with open(r"C:\Users\soumy\.gemini\antigravity\brain\052b6941-8990-4a8d-a6bc-a50464cc197d\.system_generated\logs\transcript.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        if item.get("source") == "USER_EXPLICIT" or item.get("type") == "USER_INPUT":
            step = item.get("step_index")
            if step in [3391, 3504, 3651, 3872, 3968, 3969, 4027, 4071]:
                print(f"=== STEP {step} ===")
                c = item.get("content")
                if isinstance(c, list):
                    for sub in c:
                        if isinstance(sub, dict) and sub.get("text"):
                            print(sub.get("text"))
                else:
                    print(c)

