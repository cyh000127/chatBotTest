from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import asin, cos, radians, sin, sqrt

from PROJECT.evidence.metadata import extract_artifact_metadata
from PROJECT.storage.evidence import EvidenceSubmission, EvidenceSubmissionSession

SIGNAL_EXIF_PRESENT = "exif_present"
SIGNAL_GPS_PRESENT = "gps_present"
SIGNAL_CAPTURE_TIME_PRESENT = "capture_time_present"
SIGNAL_CAPTURE_TIME = "capture_time"
SIGNAL_GPS_LATITUDE = "gps_latitude"
SIGNAL_GPS_LONGITUDE = "gps_longitude"
SIGNAL_LOCATION_DISTANCE_METERS = "location_distance_meters"
SIGNAL_UPLOAD_DELAY_SECONDS = "upload_delay_seconds"

SIGNAL_STATUS_PRESENT = "present"
SIGNAL_STATUS_MISSING = "missing"
SIGNAL_STATUS_COMPUTED = "computed"
SIGNAL_STATUS_NOT_COMPUTED = "not_computed"


@dataclass(frozen=True)
class EvidenceSignalCandidate:
    signal_type_code: str
    signal_status_code: str
    numeric_value: float | None = None
    text_value: str | None = None
    detail: dict | None = None


@dataclass(frozen=True)
class EvidenceSignalExtractionResult:
    evidence_submission_id: str
    signals: tuple[EvidenceSignalCandidate, ...]


def extract_signal_candidates(
    submission: EvidenceSubmission,
    session: EvidenceSubmissionSession,
) -> EvidenceSignalExtractionResult:
    payload = submission.payload if isinstance(submission.payload, dict) else {}
    artifact_metadata = extract_artifact_metadata(submission.staged_artifact_uri)
    exif_payload = payload.get("exif")
    metadata_payload = payload.get("metadata")
    exif = exif_payload if isinstance(exif_payload, dict) else {}
    metadata = metadata_payload if isinstance(metadata_payload, dict) else {}
    gps_payload = payload.get("gps")
    gps = gps_payload if isinstance(gps_payload, dict) else {}

    if artifact_metadata is not None and artifact_metadata.usable:
        exif_present = artifact_metadata.exif_present
        exif_detail = artifact_metadata.detail
    else:
        explicit_exif_present = _parse_bool(payload.get("exif_present"))
        if explicit_exif_present is None:
            exif_present = bool(exif)
        else:
            exif_present = explicit_exif_present
        exif_detail = artifact_metadata.detail if artifact_metadata is not None else {"source": "submission_payload"}

    artifact_capture_time = artifact_metadata.captured_at if artifact_metadata is not None and artifact_metadata.usable else None
    capture_time_raw = _first_value(
        artifact_capture_time,
        submission.captured_at,
        exif.get("captured_at"),
        exif.get("capture_time"),
        metadata.get("captured_at"),
        payload.get("captured_at"),
    )
    capture_time = _parse_datetime(capture_time_raw)

    gps_latitude = _first_float(
        artifact_metadata.gps_latitude if artifact_metadata is not None and artifact_metadata.usable else None,
        exif.get("gps_latitude"),
        metadata.get("gps_latitude"),
        gps.get("latitude"),
        payload.get("gps_latitude"),
    )
    gps_longitude = _first_float(
        artifact_metadata.gps_longitude if artifact_metadata is not None and artifact_metadata.usable else None,
        exif.get("gps_longitude"),
        metadata.get("gps_longitude"),
        gps.get("longitude"),
        payload.get("gps_longitude"),
    )
    gps_present = gps_latitude is not None and gps_longitude is not None
    gps_detail = artifact_metadata.detail if artifact_metadata is not None and artifact_metadata.usable else {"source": "submission_payload"}
    capture_detail = (
        {"source": "staged_artifact", "raw_value": capture_time_raw.isoformat()}
        if artifact_capture_time is not None
        else (
            {"source": "submission_payload", "raw_value": capture_time_raw}
            if capture_time_raw is not None
            else (
                {**artifact_metadata.detail, "raw_value": None}
                if artifact_metadata is not None
                else {"source": "submission_payload", "raw_value": None}
            )
        )
    )

    signals = [
        EvidenceSignalCandidate(
            signal_type_code=SIGNAL_EXIF_PRESENT,
            signal_status_code=SIGNAL_STATUS_PRESENT if exif_present else SIGNAL_STATUS_MISSING,
            detail=exif_detail,
        ),
        EvidenceSignalCandidate(
            signal_type_code=SIGNAL_GPS_PRESENT,
            signal_status_code=SIGNAL_STATUS_PRESENT if gps_present else SIGNAL_STATUS_MISSING,
            detail=gps_detail,
        ),
        EvidenceSignalCandidate(
            signal_type_code=SIGNAL_CAPTURE_TIME_PRESENT,
            signal_status_code=SIGNAL_STATUS_PRESENT if capture_time is not None else SIGNAL_STATUS_MISSING,
            detail=capture_detail,
        ),
        EvidenceSignalCandidate(
            signal_type_code=SIGNAL_CAPTURE_TIME,
            signal_status_code=SIGNAL_STATUS_PRESENT if capture_time is not None else SIGNAL_STATUS_MISSING,
            text_value=capture_time.isoformat() if capture_time is not None else None,
            detail=capture_detail,
        ),
        EvidenceSignalCandidate(
            signal_type_code=SIGNAL_GPS_LATITUDE,
            signal_status_code=SIGNAL_STATUS_PRESENT if gps_latitude is not None else SIGNAL_STATUS_MISSING,
            numeric_value=gps_latitude,
            detail=gps_detail,
        ),
        EvidenceSignalCandidate(
            signal_type_code=SIGNAL_GPS_LONGITUDE,
            signal_status_code=SIGNAL_STATUS_PRESENT if gps_longitude is not None else SIGNAL_STATUS_MISSING,
            numeric_value=gps_longitude,
            detail=gps_detail,
        ),
    ]

    if gps_present and session.accepted_location_latitude is not None and session.accepted_location_longitude is not None:
        distance_meters = _haversine_distance_meters(
            session.accepted_location_latitude,
            session.accepted_location_longitude,
            gps_latitude,
            gps_longitude,
        )
        signals.append(
            EvidenceSignalCandidate(
                signal_type_code=SIGNAL_LOCATION_DISTANCE_METERS,
                signal_status_code=SIGNAL_STATUS_COMPUTED,
                numeric_value=distance_meters,
                detail={
                    "accepted_location_latitude": session.accepted_location_latitude,
                    "accepted_location_longitude": session.accepted_location_longitude,
                },
            )
        )
    else:
        signals.append(
            EvidenceSignalCandidate(
                signal_type_code=SIGNAL_LOCATION_DISTANCE_METERS,
                signal_status_code=SIGNAL_STATUS_NOT_COMPUTED,
                detail={"reason": "gps_or_accepted_location_missing"},
            )
        )

    uploaded_at = _parse_datetime(submission.uploaded_at)
    if capture_time is not None and uploaded_at is not None:
        signals.append(
            EvidenceSignalCandidate(
                signal_type_code=SIGNAL_UPLOAD_DELAY_SECONDS,
                signal_status_code=SIGNAL_STATUS_COMPUTED,
                numeric_value=(uploaded_at - capture_time).total_seconds(),
                detail={
                    "captured_at": capture_time.isoformat(),
                    "uploaded_at": uploaded_at.isoformat(),
                },
            )
        )
    else:
        signals.append(
            EvidenceSignalCandidate(
                signal_type_code=SIGNAL_UPLOAD_DELAY_SECONDS,
                signal_status_code=SIGNAL_STATUS_NOT_COMPUTED,
                detail={"reason": "capture_time_or_uploaded_at_missing"},
            )
        )

    return EvidenceSignalExtractionResult(
        evidence_submission_id=submission.id,
        signals=tuple(signals),
    )


def _first_value(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _parse_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return None


def _first_float(*values) -> float | None:
    for value in values:
        parsed = _parse_float(value)
        if parsed is not None:
            return parsed
    return None


def _parse_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _parse_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = datetime.fromisoformat(stripped.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    return None


def _haversine_distance_meters(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    earth_radius_meters = 6_371_000
    lat_a = radians(latitude_a)
    lon_a = radians(longitude_a)
    lat_b = radians(latitude_b)
    lon_b = radians(longitude_b)
    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a
    root = sin(delta_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_meters * asin(sqrt(root))
