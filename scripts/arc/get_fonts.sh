#!/usr/bin/env bash
# Download the Japanese fonts of the archive videos (npm packages @fontsource-variable/noto-serif-jp and
# noto-sans-jp, pinned) into <dir>/noto-serif-jp and <dir>/noto-sans-jp for scripts/arc/fonts.py.
# Usage: scripts/arc/get_fonts.sh <dir>
set -euo pipefail
mkdir -p "$1" && cd "$1"
for p in noto-serif-jp noto-sans-jp; do
  [ -f "$p/index.css" ] && continue
  npm pack -q "@fontsource-variable/$p@5.3.1" >/dev/null
  mkdir -p "$p" && tar -xzf "fontsource-variable-$p-5.3.1.tgz" -C "$p" --strip-components=1
done
ls "$1"
