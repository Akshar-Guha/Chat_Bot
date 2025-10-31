from pathlib import Path
import json

# Simple test of just the structure
frontend_dir = Path('s:/projects/Project-1/src/frontend')
package_json = frontend_dir / 'package.json'

if package_json.exists():
    print('✓ package.json exists')
    try:
        with open(package_json, 'r', encoding='utf-8') as f:
            package = json.load(f)
        print(f'✓ package.json loaded: {len(package.get("dependencies", {}))} dependencies')
    except Exception as e:
        print(f'✗ Error loading package.json: {e}')
else:
    print('✗ package.json not found')
