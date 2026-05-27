# forensic. — AI Credibility Verifier

Python + Flask clone of the [AI Credibility Check](https://ai-credibility-check.preview.emergentagent.com/) workflow: image & text forensic scans powered by **Google Gemini**.

## Features (matching the reference app)

- **Image scan** — upload JPEG/PNG/WEBP (max 10 MB), optional caption, 3-pass analysis
- **Text scan** — paste headline or claim
- **Three passes** — pixel forensics, claim reasoning, weighted verdict (0–100 score)
- **Image metadata** — description + estimated creation/publish date (EXIF when available)
- **Method & FAQ** sections on the same page

## Setup

```powershell
cd "c:\Users\Shivangi\OneDrive\Desktop\fake news"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

Run:

```powershell
python app.py
```

Open **http://10.10.10.89:5000/**

## Note on the Emergent link

The live preview URL only serves a **built** React app (minified JavaScript). Original source is inside [Emergent](https://app.emergent.sh/) if you own that project. This repo is a **readable Python reimplementation** with the same UX and analysis flow.
