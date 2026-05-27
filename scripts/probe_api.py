import re
import sys
from pathlib import Path

import urllib.request

BASE = "https://ai-credibility-check.preview.emergentagent.com"

if len(sys.argv) > 1:
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    hits = sorted(
        set(re.findall(r"/api/[a-zA-Z0-9_/-]+", text))
        | set(re.findall(r"api/[a-zA-Z0-9_/-]+", text))
    )
    print("From bundle:")
    for h in hits:
        print(" ", h)

candidates = [
    "/api/",
    "/api/forensics",
    "/api/forensic",
    "/api/verify",
    "/api/verify-image",
    "/api/verify/text",
    "/api/verify/image",
    "/api/check-credibility",
    "/api/scanner",
    "/api/v1/verify",
]

print("\nHTTP probe:")
for path in candidates:
    url = BASE + path
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read(200).decode("utf-8", errors="replace")
            print(f"{path} -> {resp.status} {body[:120]}")
    except Exception as exc:
        print(f"{path} -> {exc}")
