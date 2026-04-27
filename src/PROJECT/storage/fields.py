from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from PROJECT.fields.geometry import bounding_box, centroid, normalize_polygon
from PROJECT.storage.invitations import DEFAULT_LOCAL_PROJECT_ID, utc_now_text

FIELD_REGISTRY_STATUS_DRAFT = "draft"
FIELD_REGISTRY_STATUS_PUBLISHED = "published"
FIELD_REGISTRY_STATUS_ARCHIVED = "archived"


@dataclass(frozen=True)
class FieldRegistryVersion:
    id: str
    project_id: str
    version_label: str
    source_code: str
    version_status_code: str
    published_at: str | None
    archived_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FieldRegistryField:
    id: str
    field_registry_version_id: str
    project_id: str
    field_code: str
    display_name: str
    area_square_meters: float | None
    metadata_json: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FieldRegistryBoundary:
    id: str
    field_id: str
    polygon_json: str
    bounding_box_json: str
    centroid_latitude: float
    centroid_longitude: float
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FieldRegistryFieldRecord:
    field: FieldRegistryField
    boundary: FieldRegistryBoundary

    @property
    def polygon(self) -> tuple[tuple[float, float], ...]:
        payload = json.loads(self.boundary.polygon_json)
        return tuple((float(lat), float(lng)) for lat, lng in payload)

    @property
    def bbox(self) -> dict[str, float]:
        payload = json.loads(self.boundary.bounding_box_json)
        return {key: float(value) for key, value in payload.items()}


class SqliteFieldRegistryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def create_registry_version(
        self,
        *,
        version_label: str,
        project_id: str = DEFAULT_LOCAL_PROJECT_ID,
        source_code: str = "local_runtime",
    ) -> FieldRegistryVersion:
        with self._lock:
            now = utc_now_text()
            version_id = f"field_version_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO field_registry_versions (
                  id,
                  project_id,
                  version_label,
                  source_code,
                  version_status_code,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    project_id,
                    version_label,
                    source_code,
                    FIELD_REGISTRY_STATUS_DRAFT,
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_registry_version(version_id)
            if created is None:
                raise RuntimeError("생성한 농지 레지스트리 버전을 다시 읽을 수 없습니다.")
            return created

    def publish_version(self, version_id: str) -> FieldRegistryVersion:
        with self._lock:
            version = self._require_version(version_id)
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE field_registry_versions
                SET version_status_code = ?,
                    archived_at = ?,
                    updated_at = ?
                WHERE project_id = ?
                  AND version_status_code = ?
                  AND id <> ?
                """,
                (
                    FIELD_REGISTRY_STATUS_ARCHIVED,
                    now,
                    now,
                    version.project_id,
                    FIELD_REGISTRY_STATUS_PUBLISHED,
                    version_id,
                ),
            )
            self._connection.execute(
                """
                UPDATE field_registry_versions
                SET version_status_code = ?,
                    published_at = COALESCE(published_at, ?),
                    archived_at = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    FIELD_REGISTRY_STATUS_PUBLISHED,
                    now,
                    now,
                    version_id,
                ),
            )
            self._connection.commit()
            return self._require_version(version_id)

    def import_field(
        self,
        *,
        field_registry_version_id: str,
        field_code: str,
        display_name: str,
        polygon: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        area_square_meters: float | None = None,
        metadata: dict | None = None,
    ) -> FieldRegistryFieldRecord:
        with self._lock:
            version = self._require_version(field_registry_version_id)
            normalized_polygon = normalize_polygon(list(polygon))
            bbox = bounding_box(normalized_polygon)
            center_latitude, center_longitude = centroid(normalized_polygon)
            now = utc_now_text()
            field_id = f"field_{uuid4().hex}"
            boundary_id = f"field_boundary_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO field_registry_fields (
                  id,
                  field_registry_version_id,
                  project_id,
                  field_code,
                  display_name,
                  area_square_meters,
                  metadata_json,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    field_id,
                    version.id,
                    version.project_id,
                    field_code,
                    display_name,
                    area_square_meters,
                    json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            self._connection.execute(
                """
                INSERT INTO field_registry_boundaries (
                  id,
                  field_id,
                  polygon_json,
                  bounding_box_json,
                  centroid_latitude,
                  centroid_longitude,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    boundary_id,
                    field_id,
                    json.dumps(normalized_polygon, ensure_ascii=False),
                    json.dumps(bbox, ensure_ascii=False, sort_keys=True),
                    center_latitude,
                    center_longitude,
                    now,
                    now,
                ),
            )
            self._connection.commit()
            return self.get_field_record(field_id)

    def get_registry_version(self, version_id: str) -> FieldRegistryVersion | None:
        row = self._connection.execute(
            "SELECT * FROM field_registry_versions WHERE id = ?",
            (version_id,),
        ).fetchone()
        if row is None:
            return None
        return FieldRegistryVersion(**dict(row))

    def latest_published_version(self, *, project_id: str = DEFAULT_LOCAL_PROJECT_ID) -> FieldRegistryVersion | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM field_registry_versions
            WHERE project_id = ?
              AND version_status_code = ?
            ORDER BY published_at DESC, created_at DESC
            LIMIT 1
            """,
            (project_id, FIELD_REGISTRY_STATUS_PUBLISHED),
        ).fetchone()
        if row is None:
            return None
        return FieldRegistryVersion(**dict(row))

    def list_fields_for_version(self, version_id: str) -> tuple[FieldRegistryFieldRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT
              f.id AS field_id,
              f.field_registry_version_id,
              f.project_id,
              f.field_code,
              f.display_name,
              f.area_square_meters,
              f.metadata_json,
              f.created_at AS field_created_at,
              f.updated_at AS field_updated_at,
              b.id AS boundary_id,
              b.field_id AS boundary_field_id,
              b.polygon_json,
              b.bounding_box_json,
              b.centroid_latitude,
              b.centroid_longitude,
              b.created_at AS boundary_created_at,
              b.updated_at AS boundary_updated_at
            FROM field_registry_fields f
            JOIN field_registry_boundaries b ON b.field_id = f.id
            WHERE f.field_registry_version_id = ?
            ORDER BY f.field_code ASC
            """,
            (version_id,),
        ).fetchall()
        return tuple(_field_record_from_row(row) for row in rows)

    def list_published_fields(
        self,
        *,
        project_id: str = DEFAULT_LOCAL_PROJECT_ID,
    ) -> tuple[FieldRegistryFieldRecord, ...]:
        version = self.latest_published_version(project_id=project_id)
        if version is None:
            return ()
        return self.list_fields_for_version(version.id)

    def get_field_record(self, field_id: str) -> FieldRegistryFieldRecord:
        row = self._connection.execute(
            """
            SELECT
              f.id AS field_id,
              f.field_registry_version_id,
              f.project_id,
              f.field_code,
              f.display_name,
              f.area_square_meters,
              f.metadata_json,
              f.created_at AS field_created_at,
              f.updated_at AS field_updated_at,
              b.id AS boundary_id,
              b.field_id AS boundary_field_id,
              b.polygon_json,
              b.bounding_box_json,
              b.centroid_latitude,
              b.centroid_longitude,
              b.created_at AS boundary_created_at,
              b.updated_at AS boundary_updated_at
            FROM field_registry_fields f
            JOIN field_registry_boundaries b ON b.field_id = f.id
            WHERE f.id = ?
            """,
            (field_id,),
        ).fetchone()
        if row is None:
            raise ValueError("농지 레코드를 찾을 수 없습니다.")
        return _field_record_from_row(row)

    def get_published_field_by_code(
        self,
        *,
        field_code: str,
        project_id: str = DEFAULT_LOCAL_PROJECT_ID,
    ) -> FieldRegistryFieldRecord | None:
        row = self._connection.execute(
            """
            SELECT
              f.id AS field_id,
              f.field_registry_version_id,
              f.project_id,
              f.field_code,
              f.display_name,
              f.area_square_meters,
              f.metadata_json,
              f.created_at AS field_created_at,
              f.updated_at AS field_updated_at,
              b.id AS boundary_id,
              b.field_id AS boundary_field_id,
              b.polygon_json,
              b.bounding_box_json,
              b.centroid_latitude,
              b.centroid_longitude,
              b.created_at AS boundary_created_at,
              b.updated_at AS boundary_updated_at
            FROM field_registry_fields f
            JOIN field_registry_versions v ON v.id = f.field_registry_version_id
            JOIN field_registry_boundaries b ON b.field_id = f.id
            WHERE f.project_id = ?
              AND f.field_code = ?
              AND v.version_status_code = ?
            ORDER BY v.published_at DESC, v.created_at DESC
            LIMIT 1
            """,
            (project_id, field_code, FIELD_REGISTRY_STATUS_PUBLISHED),
        ).fetchone()
        if row is None:
            return None
        return _field_record_from_row(row)

    def _require_version(self, version_id: str) -> FieldRegistryVersion:
        version = self.get_registry_version(version_id)
        if version is None:
            raise ValueError("농지 레지스트리 버전을 찾을 수 없습니다.")
        return version


def _field_record_from_row(row: sqlite3.Row) -> FieldRegistryFieldRecord:
    payload = dict(row)
    field = FieldRegistryField(
        id=str(payload["field_id"]),
        field_registry_version_id=str(payload["field_registry_version_id"]),
        project_id=str(payload["project_id"]),
        field_code=str(payload["field_code"]),
        display_name=str(payload["display_name"]),
        area_square_meters=float(payload["area_square_meters"]) if payload["area_square_meters"] is not None else None,
        metadata_json=str(payload["metadata_json"]),
        created_at=str(payload["field_created_at"]),
        updated_at=str(payload["field_updated_at"]),
    )
    boundary = FieldRegistryBoundary(
        id=str(payload["boundary_id"]),
        field_id=str(payload["boundary_field_id"]),
        polygon_json=str(payload["polygon_json"]),
        bounding_box_json=str(payload["bounding_box_json"]),
        centroid_latitude=float(payload["centroid_latitude"]),
        centroid_longitude=float(payload["centroid_longitude"]),
        created_at=str(payload["boundary_created_at"]),
        updated_at=str(payload["boundary_updated_at"]),
    )
    return FieldRegistryFieldRecord(field=field, boundary=boundary)
