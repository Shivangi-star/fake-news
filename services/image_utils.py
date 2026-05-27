from datetime import datetime
from io import BytesIO

from PIL import Image
from PIL.ExifTags import TAGS

EXIF_DATE_TAGS = (
    "DateTimeOriginal",
    "DateTimeDigitized",
    "DateTime",
)


def extract_exif_date(image_bytes: bytes) -> str | None:
    try:
        image = Image.open(BytesIO(image_bytes))
        exif = image.getexif()
        if not exif:
            return None

        labeled = {TAGS.get(k, k): v for k, v in exif.items()}
        for tag in EXIF_DATE_TAGS:
            raw = labeled.get(tag)
            if not raw:
                continue
            parsed = _parse_exif_datetime(str(raw))
            if parsed:
                return parsed.strftime("%Y-%m-%d")
        return None
    except Exception:
        return None


def _parse_exif_datetime(value: str) -> datetime | None:
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None
