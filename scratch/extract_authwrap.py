import subprocess

res = subprocess.run(['git', 'show', '05145c2:frontend/index.html'], capture_output=True, text=True, encoding='utf-8')
html = res.stdout
start = html.find('id="authWrap"')
div_start = html.rfind('<div', 0, start)
end = html.find('id="dashboardWrap"')
div_end = html.rfind('<div', 0, end)

with open('scratch/authwrap_extracted.html', 'w', encoding='utf-8') as f:
    f.write(html[div_start:div_end])

print(f"Extracted {div_end - div_start} bytes to scratch/authwrap_extracted.html")

