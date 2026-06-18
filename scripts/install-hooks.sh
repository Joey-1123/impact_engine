#!/bin/sh
# Install impact-engine git hooks into the current repository
# Usage: sh scripts/install-hooks.sh [--force]

set -e

HOOK_DIR=$(git rev-parse --git-dir 2>/dev/null || echo ".git")
HOOKS_SOURCE="$(dirname "$0")/git-hooks"
FORCE="${1:-}"

if [ ! -d "$HOOKS_SOURCE" ]; then
    echo "Error: hooks source directory not found at $HOOKS_SOURCE"
    echo "Run this script from the project root: sh scripts/install-hooks.sh"
    exit 1
fi

for hook in pre-commit; do
    TARGET="$HOOK_DIR/hooks/$hook"
    if [ -f "$TARGET" ] && [ "$FORCE" != "--force" ]; then
        echo "Skipping $hook (already exists). Use --force to overwrite."
    else
        cp "$HOOKS_SOURCE/$hook" "$TARGET"
        chmod +x "$TARGET"
        echo "Installed $hook hook"
    fi
done

echo "Done. impact-engine hooks are active."
