import os

def get_python_files(base_dir):
    python_files = []
    
    # Folders we NEVER want to scan
    ignore_dirs = {".venv", "venv", "env", ".git", "__pycache__", "node_modules", "build", "dist"}

    for root, dirs, files in os.walk(base_dir):
        # Modify dirs in-place to prevent os.walk from even entering ignored folders
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    return python_files