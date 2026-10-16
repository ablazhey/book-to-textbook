#!/usr/bin/env bash
# Installs the kit into a project: copies .claude/workflows and .claude/skills/make-book.
# Uploads nothing and touches no files outside the target folder.
#
#   ./install.sh                 # into the current folder
#   ./install.sh ~/books-project # into the given folder (created if missing)
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$PWD}"
mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"

if [ "$TARGET" = "$KIT" ]; then
  echo "Target folder is the kit folder itself — pick another: ./install.sh <project folder>" >&2
  exit 1
fi
command -v python3 >/dev/null || { echo "python3 is required." >&2; exit 1; }

mkdir -p "$TARGET/.claude/workflows/scripts" "$TARGET/.claude/skills/make-book"

copy() { # copy <src> <dst>: never overwrite an existing, different file silently
  local src="$1" dst="$2"
  if [ -e "$dst" ] && ! cmp -s "$src" "$dst"; then
    cp "$dst" "$dst.bak"
    echo "  updated (old one saved as $(basename "$dst").bak): ${dst#"$TARGET"/}"
  else
    echo "  ok: ${dst#"$TARGET"/}"
  fi
  cp "$src" "$dst"
}

echo "Installing into $TARGET"
for f in "$KIT"/.claude/workflows/*.js; do copy "$f" "$TARGET/.claude/workflows/$(basename "$f")"; done
for f in "$KIT"/.claude/workflows/scripts/*.py; do copy "$f" "$TARGET/.claude/workflows/scripts/$(basename "$f")"; done
copy "$KIT/.claude/skills/make-book/SKILL.md" "$TARGET/.claude/skills/make-book/SKILL.md"

python3 -c "import pypdf" 2>/dev/null || echo "Note: PDF books need pypdf:  pip3 install pypdf  (not needed for epub)"

cat <<EOF

Done. Next:
  1) cd "$TARGET" && claude
  2) /make-book path/to/book.epub
The result appears in courses/<slug>/textbook.html — open it with a double click.
EOF
