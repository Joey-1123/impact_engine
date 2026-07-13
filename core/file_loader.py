# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import os
from typing import List, Optional, Set

try:
    import pathspec
except ImportError:
    pathspec = None


def _load_gitignore(base_dir: str) -> Optional[object]:
    if pathspec is None:
        return None
    gitignore_path = os.path.join(base_dir, ".gitignore")
    if os.path.isfile(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                return pathspec.PathSpec.from_lines("gitignore", f.readlines())
        except PermissionError:
            return None
    return None


def get_python_files(base_dir: str, respect_gitignore: bool = True) -> List[str]:
    return get_code_files(base_dir, {".py"}, respect_gitignore=respect_gitignore)


def get_code_files(base_dir: str, extensions: Set[str] | None = None, respect_gitignore: bool = True) -> List[str]:
    if extensions is None:
        from core.parsers import list_supported_extensions
        extensions = set(list_supported_extensions())

    code_files: List[str] = []

    ignore_dirs = {".venv", "venv", "env", ".git", "__pycache__", "node_modules", "build", "dist"}

    spec = _load_gitignore(base_dir) if respect_gitignore else None

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]

        rel_root = os.path.relpath(root, base_dir)
        if rel_root == ".":
            rel_root = ""

        if spec:
            dirs[:] = [
                d for d in dirs
                if not spec.match_file(os.path.join(rel_root, d) if rel_root else d)
            ]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in extensions:
                continue
            file_path = os.path.join(root, file)
            rel_path = os.path.join(rel_root, file) if rel_root else file
            if spec and spec.match_file(rel_path):
                continue
            code_files.append(file_path)

    return code_files
