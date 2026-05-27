import re
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/bundle.js")
text = path.read_text(encoding="utf-8", errors="ignore")

paths = sorted(
    set(re.findall(r'["\'](/api[a-zA-Z0-9_/-]+)["\']', text))
    | set(re.findall(r"forensic[a-zA-Z0-9_/-]+", text))
)
print("API paths:")
for p in paths:
    print(" ", p)

routes = sorted(set(re.findall(r'["\'](/[a-z][a-z0-9/-]{3,50})["\']', text)))
print("\nRoutes with api/verify/scan/check:")
for r in routes:
    if any(k in r for k in ("api", "verify", "scan", "check", "forensic")):
        print(" ", r)

keywords = ("credib", "fake", "news", "image", "verdict", "gemini", "check", "upload", "forensic")
strings = re.findall(r'["\']([A-Za-z][^"\']{20,100})["\']', text)
seen = set()
for s in strings:
    low = s.lower()
    if any(k in low for k in keywords) and s not in seen:
        seen.add(s)
        print(s)
