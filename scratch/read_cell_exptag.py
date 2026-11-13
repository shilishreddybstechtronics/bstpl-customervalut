with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('const cell =')
print("--- CELL FUNCTION ---")
print(text[pos:pos+1000])

pos2 = text.find('const expTag =')
if pos2 == -1:
    pos2 = text.find('function expTag(')
print("--- EXPTAG FUNCTION ---")
print(text[pos2:pos2+1000])

