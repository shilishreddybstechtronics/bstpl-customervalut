with open('frontend/home.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('async function runLiveCycle(')
print(text[pos+1000:pos+3500])

