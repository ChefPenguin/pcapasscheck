#!/usr/bin/env bash
# check_wordlist.sh — exact-line membership test via grep
# Usage: echo -n "plaintext" | ./check_wordlist.sh /path/to/wordlist [--ignore-case]
set -Eeuo pipefail

WORDLIST="${1:?Usage: check_wordlist.sh /path/to/wordlist [--ignore-case]}"
ICASE="${2:-}"

# Read exactly one line from stdin; keep it even if there's no trailing newline.
IFS= read -r PATTERN || true

# Reject truly empty input to avoid empty-pattern => match-all
if [[ -z "$PATTERN" ]]; then
  exit 1
fi

flags=(-xF -m1)
[[ "$ICASE" == "--ignore-case" ]] && flags=(-i "${flags[@]}")

# Use a here-string to feed the pattern file to grep (-f -), search WORDLIST
LC_ALL=C LANG=C grep "${flags[@]}" -f - -- "$WORDLIST" >/dev/null <<<"$PATTERN"
