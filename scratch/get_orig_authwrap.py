import subprocess

res = subprocess.run(['git', 'show', '05145c2:frontend/index.html'], capture_output=True, text=True, encoding='utf-8')
html = res.stdout
start = html.find('id="authWrap"')
div_start = html.rfind('<div', 0, start)
end = html.find('id="dashboardWrap"')
div_end = html.rfind('<div', 0, end)

print(f"authWrap found from {div_start} to {div_end} ({div_end - div_start} chars)")
print("HEAD:")
print(html[div_start:div_start+500])
print("\nTAIL:")
print(html[div_end-400:div_end])

