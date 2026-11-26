"""Apply only the company SCBS relay exception to the pinned auth-server base."""

import sys
from pathlib import Path

source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/app/server.py")
old = 'frozenset({"airegistry-tools"})'
new = 'frozenset({"airegistry-tools", "itg-scbs"})'
text = source.read_text(encoding="utf-8")
if text.count(old) != 1:
    raise SystemExit("Unexpected auth-server base; refuse to patch")
source.write_text(text.replace(old, new), encoding="utf-8")
