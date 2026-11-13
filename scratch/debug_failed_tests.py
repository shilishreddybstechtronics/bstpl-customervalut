with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    inv = f.read()

print("inv 'data-editdev':", 'data-editdev' in inv)
print("inv 'data-del':", 'data-del' in inv)
print("inv 'invTableWrap':", 'invTableWrap' in inv)
print("inv 'invTableWrap.onclick':", 'invTableWrap.onclick' in inv)
idx = inv.find('data-editdev')
print(inv[idx:idx+400])

with open('frontend/settings.html', 'r', encoding='utf-8') as f:
    st = f.read()

print("settings 'settingsBtnLogout':", 'settingsBtnLogout' in st)
print("settings 'handleSettingsLogout':", 'handleSettingsLogout' in st)
idx2 = st.find('settingsBtnLogout')
print("idx2 of settingsBtnLogout:", idx2)

