with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos_dash = text.find('id="dashboardWrap"')
pos_home = text.find('id="box-home"')

print('dashboardWrap at:', pos_dash)
print('box-home at:', pos_home)
print('Is box-home inside dashboardWrap?', pos_home > pos_dash)

# Let's find closing </div> of dashboardWrap
# Let's check indentation or structure of dashboardWrap
pos_script = text.find('<script', pos_dash)
print('Script tag after dashboardWrap at:', pos_script)
dashboard_content = text[pos_dash:pos_script]
print('Length of dashboard content:', len(dashboard_content))

