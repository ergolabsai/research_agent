#!/usr/bin/env bash
#
# stamp-headers.sh — add SPDX + copyright headers to all source files.
#
# The whole ErgoLabs repo is AGPL-3.0-only. This script stamps every
# source file you authored with:
#
#   SPDX-License-Identifier: AGPL-3.0-only
#   SPDX-FileCopyrightText: 2026 <Your Name> and <JR's Full Name>
#
# It is idempotent: running it again will not duplicate headers on files
# that already have them (reuse annotate --skip-existing).
#
# Requirements:
#   pipx install reuse        # or: pip install --user reuse
#
# Usage:
#   ./scripts/stamp-headers.sh          # stamp files
#   ./scripts/stamp-headers.sh --check  # verify only (use this in CI)
#
# IMPORTANT: edit COPYRIGHT below before first run, and review the
# EXCLUDE list so vendored/generated code is never stamped.

set -euo pipefail

# ---- EDIT THESE TWO LINES --------------------------------------------
COPYRIGHT_HOLDER="Chelsea Liekhus-Schmaltz and Johnathon Barhydt"
COPYRIGHT_YEAR="2026"
# ----------------------------------------------------------------------

LICENSE_ID="AGPL-3.0-only"

# Paths to NEVER stamp (vendored / generated / third-party / binary).
# Add to this list to match your repository.
EXCLUDE_DIRS=(
  ".git"
  "vendor"
  "node_modules"
  "third_party"
  "dist"
  "build"
  "target"
  ".venv"
)

# Source extensions to stamp. Add languages as needed.
INCLUDE_EXTS=(
  "go" "py" "js" "jsx" "ts" "tsx" "rs" "java" "c" "h" "cc" "cpp" "hpp"
  "rb" "sh" "css" "scss"
)

if ! command -v reuse >/dev/null 2>&1; then
  echo "error: 'reuse' not found. Install with: pipx install reuse" >&2
  exit 1
fi

if [[ "${1:-}" == "--check" ]]; then
  echo "Verifying license headers across the repository..."
  exec reuse lint
fi

# Build a find expression honoring the exclude list.
prune_args=()
for d in "${EXCLUDE_DIRS[@]}"; do
  prune_args+=( -path "./$d" -prune -o )
done

name_args=()
for i in "${!INCLUDE_EXTS[@]}"; do
  ext="${INCLUDE_EXTS[$i]}"
  if [[ $i -gt 0 ]]; then name_args+=( -o ); fi
  name_args+=( -name "*.${ext}" )
done

mapfile -t files < <(
  find . "${prune_args[@]}" \( "${name_args[@]}" \) -type f -print
)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No source files matched. Check INCLUDE_EXTS / EXCLUDE_DIRS."
  exit 0
fi

echo "Stamping ${#files[@]} files with ${LICENSE_ID}..."
reuse annotate \
  --license "$LICENSE_ID" \
  --copyright "$COPYRIGHT_HOLDER" \
  --year "$COPYRIGHT_YEAR" \
  --skip-unrecognised \
  --skip-existing \
  "${files[@]}"

echo
echo "Done. Now verify with: ./scripts/stamp-headers.sh --check"
