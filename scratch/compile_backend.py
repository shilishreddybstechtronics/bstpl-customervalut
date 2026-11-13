import os
import py_compile
import sys

backend_dir = 'backend'
files = [os.path.join(backend_dir, f) for f in os.listdir(backend_dir) if f.endswith('.py')]
has_error = False

print(f"=== Compiling all {len(files)} Python files in {backend_dir} ===")
for f in sorted(files):
    try:
        py_compile.compile(f, doraise=True)
        print(f"✓ {f} compiled cleanly.")
    except py_compile.PyCompileError as e:
        has_error = True
        print(f"✗ ERROR in {f}: {e}")

if has_error:
    sys.exit(1)
else:
    print("All backend Python files compiled successfully with ZERO errors.\n")

