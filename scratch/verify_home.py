with open('frontend/home.html', encoding='utf-8') as f:
    txt = f.read()

pos = txt.find('id="statsRibbon"')
print("statsRibbon position:", pos)
if pos != -1:
    print(txt[pos-80:pos+1600])
