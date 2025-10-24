#!/usr/bin/env bash
set -euo pipefail

# Cleanup workspace script (idempotent)
# Moves selected files into archive/ /docs_archive/ /demos/ and creates a trash/ placeholder.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p archive docs_archive demos trash

mv_if_exists() {
  local src="$1" dst="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    echo "Moving: $src -> $dst"
    mv -v "$src" "$dst"
  else
    echo "Not found (skipping): $src"
  fi
}

# Top-level docs to archive
mv_if_exists "__Brutal But Fair Code Review_ MAPE-K Water Utilit.md" "archive/__Brutal But Fair Code Review_ MAPE-K Water Utilit.md"
mv_if_exists "RESEARCH_WRITEUP.md" "archive/RESEARCH_WRITEUP.md"
mv_if_exists "INTEGRATION_COMPLETE.md" "archive/INTEGRATION_COMPLETE.md"
mv_if_exists "SOFTWARE_PRACTICES-1.md" "archive/SOFTWARE_PRACTICES-1.md"
mv_if_exists "SOFTWARE_PRACTICES.md" "archive/SOFTWARE_PRACTICES.md"
mv_if_exists "TECHNICAL_IMPLEMENTATION.md" "archive/TECHNICAL_IMPLEMENTATION.md"

# Move docs under docs/ to docs_archive/
mv_if_exists "docs/API_REFERENCE.md" "docs_archive/API_REFERENCE.md"
mv_if_exists "docs/RESEARCH_PATTERNS.md" "docs_archive/RESEARCH_PATTERNS.md"

# Move demo and quick tests into demos/
mv_if_exists "demo_patterns.py" "demos/demo_patterns.py"
mv_if_exists "demo_emergency.py" "demos/demo_emergency.py"
mv_if_exists "simple_iot_test.py" "demos/simple_iot_test.py"
mv_if_exists "examples/pattern_integration_demo.py" "demos/pattern_integration_demo.py"

# Create README placeholders for archive/trash/demos/docs_archive
for d in archive docs_archive demos trash; do
  if [ ! -e "$d/README.md" ]; then
    echo "# $d" > "$d/README.md"
    echo "This folder was created by scripts/cleanup_workspace.sh to hold moved files." >> "$d/README.md"
  fi
done

# Ensure .gitignore has entries (idempotent)
GITIGNORE_FILE=".gitignore"
ensure_gitignore_entry() {
  local entry="$1"
  if [ ! -f "$GITIGNORE_FILE" ]; then
    touch "$GITIGNORE_FILE"
  fi
  if ! grep -Fxq "$entry" "$GITIGNORE_FILE"; then
    echo "$entry" >> "$GITIGNORE_FILE"
  fi
}

ensure_gitignore_entry "/archive/"
ensure_gitignore_entry "/trash/"
ensure_gitignore_entry "/demos/"
ensure_gitignore_entry "__pycache__/"
ensure_gitignore_entry "*.pyc"
ensure_gitignore_entry ".vscode/"

echo "Cleanup script finished. Check archive/, demos/, docs_archive/ and trash/ for moved files."