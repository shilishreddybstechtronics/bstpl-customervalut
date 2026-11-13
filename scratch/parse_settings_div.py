with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<div class="settings-action-list">')
pos = start + len('<div class="settings-action-list">')
depth = 1
while depth > 0 and pos < len(text):
    if text[pos:pos+4] == '<div':
        depth += 1
        pos += 4
    elif text[pos:pos+6] == '</div>':
        depth -= 1
        pos += 6
    else:
        pos += 1

block = text[start:pos]
print("Block length:", len(block))
print("First 300 chars:")
print(block[:300])
print("Last 300 chars:")
print(block[-300:])

