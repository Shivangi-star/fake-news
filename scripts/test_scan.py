import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from services.gemini_service import analyze_text, configure
import os

key = os.getenv("GEMINI_API_KEY", "").strip()
if not key:
    print("ERROR: no GEMINI_API_KEY")
    sys.exit(1)

configure(key)
try:
    result = analyze_text("Scientists say drinking hot water cures all diseases overnight.")
    print("SUCCESS")
    print(result)
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
