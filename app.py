import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from services.gemini_service import analyze_image, analyze_text, configure, get_model_name
from services.image_utils import extract_exif_date

load_dotenv(Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MIME_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


def get_api_key() -> str | None:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key or None


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html", model_label=get_model_name().replace("gemini-", "gemini ").replace("-", " "))


@app.route("/api/")
def api_info():
    return jsonify({
        "service": "forensic-verifier",
        "model": get_model_name(),
    })


@app.route("/api/forensic/text", methods=["POST"])
@app.route("/api/analyze-text", methods=["POST"])
def api_analyze_text():
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY is not set. Add it to your .env file."}), 500

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Paste a headline, article, or claim to scan."}), 400
    if len(text) > 15000:
        return jsonify({"error": "Text is too long (max 15,000 characters)."}), 400

    try:
        configure(api_key)
        result = analyze_text(text)
        return jsonify({"ok": True, "type": "text", "result": result})
    except Exception as exc:
        return jsonify({"error": f"Forensic scan failed: {exc}"}), 500


@app.route("/api/forensic/image", methods=["POST"])
@app.route("/api/analyze-image", methods=["POST"])
def api_analyze_image():
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY is not set. Add it to your .env file."}), 500

    if "image" not in request.files:
        return jsonify({"error": "Drop or select an image first."}), 400

    file = request.files["image"]
    if not file or not file.filename:
        return jsonify({"error": "Drop or select an image first."}), 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return jsonify({"error": "Only JPEG, PNG or WEBP images are supported."}), 400

    ext = filename.rsplit(".", 1)[1].lower()
    image_bytes = file.read()
    if not image_bytes:
        return jsonify({"error": "Uploaded file is empty."}), 400

    caption = (request.form.get("caption") or "").strip()
    exif_date = extract_exif_date(image_bytes)

    try:
        configure(api_key)
        result = analyze_image(
            image_bytes=image_bytes,
            mime_type=MIME_MAP[ext],
            caption=caption,
            exif_date=exif_date,
        )
        if exif_date:
            result["exif_date"] = exif_date
        return jsonify({"ok": True, "type": "image", "result": result})
    except Exception as exc:
        return jsonify({"error": f"Forensic scan failed: {exc}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host="0.0.0.0", port=port)
