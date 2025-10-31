import os

frontend_src = "s:/projects/Project-1/src/frontend/src"

for root, dirs, files in os.walk(frontend_src):
    for file in files:
        if file.endswith(('.tsx', '.ts', '.css', '.json')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"✓ {filepath} - OK")
            except UnicodeDecodeError as e:
                print(f"✗ {filepath} - Unicode error: {e}")
            except Exception as e:
                print(f"✗ {filepath} - Error: {e}")
