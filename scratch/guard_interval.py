with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('setInterval(updateLiveStreamClock, 1000);', "if (typeof setInterval === 'function') setInterval(updateLiveStreamClock, 1000);")

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated setInterval guard in builder")

