import re
inv_text = open('frontend/inventory.html', 'r', encoding='utf-8').read()
scripts = re.findall(r'<script>(.*?)</script>', inv_text, re.DOTALL)
s2 = scripts[2]
print('count of \\(:', s2.count(r'\('))
print('count of \\):', s2.count(r'\)'))

