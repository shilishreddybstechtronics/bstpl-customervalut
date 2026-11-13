import glob

for f in glob.glob('scratch/*.py') + glob.glob('scratch/*.js'):
    try:
        with open(f, 'r', encoding='utf-8') as fp:
            c = fp.read()
            if 'livePolling' in c:
                print(f"Match in {f}")
    except:
        pass

