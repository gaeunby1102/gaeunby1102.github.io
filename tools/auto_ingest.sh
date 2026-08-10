#!/bin/bash
# Auto-ingest new PDFs from ~/Dropbox/9aeun/pdfs into the site and deploy.
# Triggered by a launchd WatchPaths agent (or run manually).
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
LOG=/tmp/pdf-ingest.log
REPO="$HOME/gaeunby1102.github.io"

# single-run lock (portable, no flock)
LOCKDIR=/tmp/gaeun-ingest.lock.d
if ! mkdir "$LOCKDIR" 2>/dev/null; then exit 0; fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

sleep 4            # let Dropbox finish writing the file
cd "$REPO" || exit 1

n=$(python3 tools/ingest_pdfs.py 2>>"$LOG")
echo "$(date '+%F %T')  scanned -> $n new" >> "$LOG"

if [ "${n:-0}" -gt 0 ]; then
  python3 tools/build_home.py >/dev/null 2>>"$LOG"
  git add -A
  if git commit -q -m "Auto-ingest ${n} new paper(s) into Starred Papers" 2>>"$LOG"; then
    if git push -q origin main 2>>"$LOG"; then
      echo "$(date '+%F %T')  pushed ${n} paper(s)" >> "$LOG"
    else
      echo "$(date '+%F %T')  PUSH FAILED (check gh auth)" >> "$LOG"
    fi
  fi
fi
