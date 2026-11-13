with open('scratch/run_comprehensive_tests.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(170, min(220, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

