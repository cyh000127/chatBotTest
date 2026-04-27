from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

EXIF_TAG_DATETIME = 306
EXIF_TAG_DATETIME_ORIGINAL = 36867
EXIF_TAG_GPS_INFO = 34853

GPS_TAG_LATITUDE_REF = 1
GPS_TAG_LATITUDE = 2
GPS_TAG_LONGITUDE_REF = 3
GPS_TAG_LONGITUDE = 4


@dataclass(frozen=True)
class ParsedEvidenceArtifactMetadata:
    parser_status_code: str
    exif_present: bool
    gps_latitude: float | None
    gps_longitude: float | None
    captured_at: datetime | None
    detail: dict

    @property
    def usable(self) -> bool:
        return self.parser_status_code == "ok"


def extract_artifact_metadata(staged_artifact_uri: str | None) -> ParsedEvidenceArtifactMetadata | None:
    if not staged_artifact_uri:
        return None

    path = artifact_uri_to_path(staged_artifact_uri)
    if path is None:
        return ParsedEvidenceArtifactMetadata(
            parser_status_code="unsupported_uri",
            exif_present=False,
            gps_latitude=None,
            gps_longitude=None,
            captured_at=None,
            detail={"source": "staged_artifact", "parser_status": "unsupported_uri"},
        )

    resolved_path = path.resolve()
    if not resolved_path.exists() or not resolved_path.is_file():
        return ParsedEvidenceArtifactMetadata(
            parser_status_code="missing_file",
            exif_present=False,
            gps_latitude=None,
            gps_longitude=None,
            captured_at=None,
            detail={"source": "staged_artifact", "parser_status": "missing_file"},
        )

    try:
        with Image.open(resolved_path) as image:
            exif = image.getexif()
            exif_present = bool(exif)
            capture_raw = exif.get(EXIF_TAG_DATETIME_ORIGINAL) or exif.get(EXIF_TAG_DATETIME)
            captured_at = _parse_exif_datetime(capture_raw)
            gps_ifd = _extract_gps_ifd(exif)
            gps_latitude = _parse_gps_coordinate(
                gps_ifd.get(GPS_TAG_LATITUDE_REF),
                gps_ifd.get(GPS_TAG_LATITUDE),
            )
            gps_longitude = _parse_gps_coordinate(
                gps_ifd.get(GPS_TAG_LONGITUDE_REF),
                gps_ifd.get(GPS_TAG_LONGITUDE),
            )
    except Exception as exc:
        return ParsedEvidenceArtifactMetadata(
            parser_status_code="read_failed",
            exif_present=False,
            gps_latitude=None,
            gps_longitude=None,
            captured_at=None,
            detail={
                "source": "staged_artifact",
                "parser_status": "read_failed",
                "error_type": type(exc).__name__,
            },
        )

    return ParsedEvidenceArtifactMetadata(
        parser_status_code="ok",
        exif_present=exif_present,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        captured_at=captured_at,
        detail={"source": "staged_artifact", "parser_status": "ok"},
    )


def artifact_uri_to_path(staged_artifact_uri: str) -> Path | None:
    parsed = urlparse(staged_artifact_uri)
    if parsed.scheme in {"", "file"}:
        if parsed.scheme == "":
            path_text = staged_artifact_uri
        else:
            path_text = unquote(parsed.path)
            if parsed.netloc:
                path_text = f"//{parsed.netloc}{path_text}"
            if len(path_text) >= 3 and path_text[0] == "/" and path_text[2] == ":":
                path_text = path_text[1:]
        return Path(path_text)
    return None


def _extract_gps_ifd(exif) -> dict:
    if not exif:
        return {}
    try:
        gps_ifd = exif.get_ifd(EXIF_TAG_GPS_INFO)
    except Exception:
        gps_ifd = exif.get(EXIF_TAG_GPS_INFO)
    return gps_ifd if isinstance(gps_ifd, dict) else {}


def _parse_exif_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    for pattern in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(stripped, pattern).replace(tzinfo=UTC)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(stripped.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_gps_coordinate(reference, value) -> float | None:
    if not reference or value is None:
        return None
    if isinstance(reference, bytes):
        reference = reference.decode("utf-8", errors="ignore")
    if not isinstance(reference, str):
        return None
    parts = list(value) if isinstance(value, (list, tuple)) else None
    if parts is None or len(parts) != 3:
        return None
    degrees = _coerce_float(parts[0])
    minutes = _coerce_float(parts[1])
    seconds = _coerce_float(parts[2])
    if degrees is None or minutes is None or seconds is None:
        return None
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if reference.upper() in {"S", "W"}:
        decimal *= -1
    return decimal


def _coerce_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    numerator = getattr(value, "numerator", None)
    denominator = getattr(value, "denominator", None)
    if numerator is not None and denominator not in {None, 0}:
        return float(numerator) / float(denominator)
    if isinstance(value, tuple) and len(value) == 2:
        top, bottom = value
        if bottom in {None, 0}:
            return None
        return float(top) / float(bottom)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
