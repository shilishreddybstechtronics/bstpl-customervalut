with open('frontend/index.html', encoding='utf-8') as f:
    content = f.read()
idx = content.find('id="settingsBtnEditName"')
print(content[idx:idx+800])

