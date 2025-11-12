import os
import shutil

def clean_python_cache(root_dir):
    """Recursively find and remove __pycache__ directories and .pyc files."""
    print(f"Starting cache cleanup in: {root_dir}")
    pycache_found = False
    pyc_found = False

    for root, dirs, files in os.walk(root_dir):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')
            print(f"Removing: {pycache_dir}")
            shutil.rmtree(pycache_dir)
            pycache_found = True

        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                print(f"Removing: {pyc_file}")
                os.remove(pyc_file)
                pyc_found = True

    if not pycache_found and not pyc_found:
        print("No Python cache files or directories found.")
    else:
        print("\nCache cleanup completed successfully.")

if __name__ == "__main__":
    # Get the directory where the script is located (project root)
    project_root = os.path.dirname(os.path.abspath(__file__))
    clean_python_cache(project_root)
    print("\nPlease restart your backend server now.")
