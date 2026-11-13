with open('scratch/run_comprehensive_tests.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(15, 65):
    print(f"{i+1}: {lines[i]}", end="")

