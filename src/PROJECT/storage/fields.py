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
FIELD_BINDING_STATUS_ACTIVE = "active"
FIELD_BINDING_STATUS_RELEASED = "released"
FIELD_BINDING_SOURCE_LOCATION = "location_match"
FIELD_BINDING_SOURCE_FIELD_CODE = "field_code"
FIELD_BINDING_EXCEPTION_STATUS_OPEN = "open"
FIELD_BINDING_EXCEPTION_STATUS_RESOLVED = "resolved"
FIELD_BINDING_EXCEPTION_STATUS_CLOSED = "closed"
FIELD_BINDING_EXCEPTION_LOCATION_NO_CANDIDATE = "location_no_candidate"
FIELD_BINDING_EXCEPTION_LOCATION_MULTIPLE_CANDIDATES = "location_multiple_candidates"
FIELD_BINDING_EXCEPTION_FIELD_CODE_NOT_FOUND = "field_code_not_found"
FIELD_BINDING_EXCEPTION_FIELD_ALREADY_BOUND = "field_already_bound"
FIELD_BINDING_EXCEPTION_PARTICIPANT_DUPLICATE = "participant_duplicate_binding"
DEFAULT_IDENTITY_PROVIDER_CODE = "telegram"
ACTIVE_ENROLLMENT_STATUS = "active"


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


@dataclass(frozen=True)
class ParticipantContext:
    participant_id: str
    participant_name: str
    project_id: str
    enrollment_id: str
    provider_user_id: str
    provider_handle: str | None


@dataclass(frozen=True)
class ParticipantFieldBinding:
    id: str
    participant_id: str
    project_id: str
    field_id: str
    field_registry_version_id: str
    binding_status_code: str
    binding_source_code: str
    onboarding_session_id: str | None
    provider_user_id: str | None
    chat_id: int | None
    location_latitude: float | None
    location_longitude: float | None
    location_accuracy_meters: float | None
    requested_field_code: str | None
    created_at: str
    updated_at: str
    deactivated_at: str | None


@dataclass(frozen=True)
class ParticipantFieldBindingRecord:
    binding: ParticipantFieldBinding
    field: FieldRegistryField
    boundary: FieldRegistryBoundary


@dataclass(frozen=True)
class FieldBindingException:
    id: str
    project_id: str
    participant_id: str | None
    onboarding_session_id: str | None
    provider_user_id: str | None
    chat_id: int | None
    field_registry_version_id: str | None
    exception_type_code: str
    exception_status_code: str
    route_hint: str
    requested_field_code: str | None
    location_latitude: float | None
    location_longitude: float | None
    location_accuracy_meters: float | None
    candidate_field_ids_json: str
    detail_json: str
    created_at: str
    updated_at: str
    resolved_at: str | None

    @property
    def candidate_field_ids(self) -> tuple[str, ...]:
        payload = json.loads(self.candidate_field_ids_json)
        return tuple(str(item) for item in payload)

    @property
    def detail(self) -> dict:
        payload = json.loads(self.detail_json)
        if isinstance(payload, dict):
            return payload
        return {}


class FieldBindingConflictError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


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

    def find_active_participant_context(self, *, provider_user_id: str) -> ParticipantContext | None:
        row = self._connection.execute(
            """
            SELECT
              p.id AS participant_id,
              p.full_name AS participant_name,
              pe.project_id,
              pe.id AS enrollment_id,
              pi.provider_user_id,
              pi.provider_handle
            FROM participant_identities pi
            JOIN participants p ON p.id = pi.participant_id
            JOIN project_enrollments pe
              ON pe.participant_id = p.id
             AND pe.enrollment_status_code = ?
            WHERE pi.identity_provider_code = ?
              AND pi.provider_user_id = ?
            ORDER BY pe.activated_at DESC, pe.created_at DESC
            LIMIT 1
            """,
            (ACTIVE_ENROLLMENT_STATUS, DEFAULT_IDENTITY_PROVIDER_CODE, provider_user_id),
        ).fetchone()
        if row is None:
            return None
        return ParticipantContext(**dict(row))

    def list_active_bindings_for_participant(
        self,
        *,
        participant_id: str,
        project_id: str,
    ) -> tuple[ParticipantFieldBindingRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT
              pb.id AS binding_id,
              pb.participant_id,
              pb.project_id,
              pb.field_id,
              pb.field_registry_version_id,
              pb.binding_status_code,
              pb.binding_source_code,
              pb.onboarding_session_id,
              pb.provider_user_id,
              pb.chat_id,
              pb.location_latitude,
              pb.location_longitude,
              pb.location_accuracy_meters,
              pb.requested_field_code,
              pb.created_at AS binding_created_at,
              pb.updated_at AS binding_updated_at,
              pb.deactivated_at,
              f.id AS field_id_row,
              f.field_registry_version_id AS field_registry_version_id_row,
              f.project_id AS field_project_id,
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
            FROM participant_field_bindings pb
            JOIN field_registry_fields f ON f.id = pb.field_id
            JOIN field_registry_boundaries b ON b.field_id = f.id
            WHERE pb.participant_id = ?
              AND pb.project_id = ?
              AND pb.binding_status_code = ?
            ORDER BY pb.created_at ASC
            """,
            (participant_id, project_id, FIELD_BINDING_STATUS_ACTIVE),
        ).fetchall()
        return tuple(_binding_record_from_row(row) for row in rows)

    def create_binding(
        self,
        *,
        participant_id: str,
        project_id: str,
        field_id: str,
        field_registry_version_id: str,
        binding_source_code: str,
        onboarding_session_id: str | None = None,
        provider_user_id: str | None = None,
        chat_id: int | None = None,
        location_latitude: float | None = None,
        location_longitude: float | None = None,
        location_accuracy_meters: float | None = None,
        requested_field_code: str | None = None,
    ) -> ParticipantFieldBindingRecord:
        with self._lock:
            existing_field_binding = self._find_active_binding_by_field_id(field_id)
            if existing_field_binding is not None and existing_field_binding.participant_id != participant_id:
                raise FieldBindingConflictError(FIELD_BINDING_EXCEPTION_FIELD_ALREADY_BOUND)
            existing_participant_binding = self._find_active_binding_for_participant_field(
                participant_id=participant_id,
                field_id=field_id,
            )
            if existing_participant_binding is not None:
                raise FieldBindingConflictError(FIELD_BINDING_EXCEPTION_PARTICIPANT_DUPLICATE)
            now = utc_now_text()
            binding_id = f"field_binding_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO participant_field_bindings (
                  id,
                  participant_id,
                  project_id,
                  field_id,
                  field_registry_version_id,
                  binding_status_code,
                  binding_source_code,
                  onboarding_session_id,
                  provider_user_id,
                  chat_id,
                  location_latitude,
                  location_longitude,
                  location_accuracy_meters,
                  requested_field_code,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    binding_id,
                    participant_id,
                    project_id,
                    field_id,
                    field_registry_version_id,
                    FIELD_BINDING_STATUS_ACTIVE,
                    binding_source_code,
                    onboarding_session_id,
                    provider_user_id,
                    chat_id,
                    location_latitude,
                    location_longitude,
                    location_accuracy_meters,
                    requested_field_code,
                    now,
                    now,
                ),
            )
            self._connection.commit()
            return self.get_binding_record(binding_id)

    def get_binding_record(self, binding_id: str) -> ParticipantFieldBindingRecord:
        row = self._connection.execute(
            """
            SELECT
              pb.id AS binding_id,
              pb.participant_id,
              pb.project_id,
              pb.field_id,
              pb.field_registry_version_id,
              pb.binding_status_code,
              pb.binding_source_code,
              pb.onboarding_session_id,
              pb.provider_user_id,
              pb.chat_id,
              pb.location_latitude,
              pb.location_longitude,
              pb.location_accuracy_meters,
              pb.requested_field_code,
              pb.created_at AS binding_created_at,
              pb.updated_at AS binding_updated_at,
              pb.deactivated_at,
              f.id AS field_id_row,
              f.field_registry_version_id AS field_registry_version_id_row,
              f.project_id AS field_project_id,
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
            FROM participant_field_bindings pb
            JOIN field_registry_fields f ON f.id = pb.field_id
            JOIN field_registry_boundaries b ON b.field_id = f.id
            WHERE pb.id = ?
            """,
            (binding_id,),
        ).fetchone()
        if row is None:
            raise ValueError("농지 바인딩을 찾을 수 없습니다.")
        return _binding_record_from_row(row)

    def create_binding_exception(
        self,
        *,
        project_id: str,
        exception_type_code: str,
        route_hint: str = "manual_resolution_required",
        participant_id: str | None = None,
        onboarding_session_id: str | None = None,
        provider_user_id: str | None = None,
        chat_id: int | None = None,
        field_registry_version_id: str | None = None,
        requested_field_code: str | None = None,
        location_latitude: float | None = None,
        location_longitude: float | None = None,
        location_accuracy_meters: float | None = None,
        candidate_field_ids: tuple[str, ...] | list[str] = (),
        detail: dict | None = None,
    ) -> FieldBindingException:
        with self._lock:
            now = utc_now_text()
            exception_id = f"field_binding_exception_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO field_binding_exceptions (
                  id,
                  project_id,
                  participant_id,
                  onboarding_session_id,
                  provider_user_id,
                  chat_id,
                  field_registry_version_id,
                  exception_type_code,
                  exception_status_code,
                  route_hint,
                  requested_field_code,
                  location_latitude,
                  location_longitude,
                  location_accuracy_meters,
                  candidate_field_ids_json,
                  detail_json,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exception_id,
                    project_id,
                    participant_id,
                    onboarding_session_id,
                    provider_user_id,
                    chat_id,
                    field_registry_version_id,
                    exception_type_code,
                    FIELD_BINDING_EXCEPTION_STATUS_OPEN,
                    route_hint,
                    requested_field_code,
                    location_latitude,
                    location_longitude,
                    location_accuracy_meters,
                    json.dumps(tuple(candidate_field_ids), ensure_ascii=False),
                    json.dumps(detail or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            self._connection.commit()
            return self.get_binding_exception(exception_id)

    def list_binding_exceptions(
        self,
        *,
        status: str | None = None,
    ) -> tuple[FieldBindingException, ...]:
        if status:
            rows = self._connection.execute(
                """
                SELECT *
                FROM field_binding_exceptions
                WHERE exception_status_code = ?
                ORDER BY created_at ASC
                """,
                (status,),
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT *
                FROM field_binding_exceptions
                ORDER BY created_at ASC
                """
            ).fetchall()
        return tuple(FieldBindingException(**dict(row)) for row in rows)

    def get_binding_exception(self, exception_id: str) -> FieldBindingException:
        row = self._connection.execute(
            "SELECT * FROM field_binding_exceptions WHERE id = ?",
            (exception_id,),
        ).fetchone()
        if row is None:
            raise ValueError("농지 바인딩 예외를 찾을 수 없습니다.")
        return FieldBindingException(**dict(row))

    def resolve_binding_exception(self, exception_id: str) -> FieldBindingException:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE field_binding_exceptions
                SET exception_status_code = ?,
                    updated_at = ?,
                    resolved_at = COALESCE(resolved_at, ?)
                WHERE id = ?
                """,
                (
                    FIELD_BINDING_EXCEPTION_STATUS_RESOLVED,
                    now,
                    now,
                    exception_id,
                ),
            )
            self._connection.commit()
            return self.get_binding_exception(exception_id)

    def _require_version(self, version_id: str) -> FieldRegistryVersion:
        version = self.get_registry_version(version_id)
        if version is None:
            raise ValueError("농지 레지스트리 버전을 찾을 수 없습니다.")
        return version

    def _find_active_binding_by_field_id(self, field_id: str) -> ParticipantFieldBinding | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM participant_field_bindings
            WHERE field_id = ?
              AND binding_status_code = ?
            LIMIT 1
            """,
            (field_id, FIELD_BINDING_STATUS_ACTIVE),
        ).fetchone()
        if row is None:
            return None
        return ParticipantFieldBinding(**dict(row))

    def _find_active_binding_for_participant_field(
        self,
        *,
        participant_id: str,
        field_id: str,
    ) -> ParticipantFieldBinding | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM participant_field_bindings
            WHERE participant_id = ?
              AND field_id = ?
              AND binding_status_code = ?
            LIMIT 1
            """,
            (participant_id, field_id, FIELD_BINDING_STATUS_ACTIVE),
        ).fetchone()
        if row is None:
            return None
        return ParticipantFieldBinding(**dict(row))


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


def _binding_record_from_row(row: sqlite3.Row) -> ParticipantFieldBindingRecord:
    payload = dict(row)
    binding = ParticipantFieldBinding(
        id=str(payload["binding_id"]),
        participant_id=str(payload["participant_id"]),
        project_id=str(payload["project_id"]),
        field_id=str(payload["field_id"]),
        field_registry_version_id=str(payload["field_registry_version_id"]),
        binding_status_code=str(payload["binding_status_code"]),
        binding_source_code=str(payload["binding_source_code"]),
        onboarding_session_id=payload["onboarding_session_id"],
        provider_user_id=payload["provider_user_id"],
        chat_id=int(payload["chat_id"]) if payload["chat_id"] is not None else None,
        location_latitude=float(payload["location_latitude"]) if payload["location_latitude"] is not None else None,
        location_longitude=float(payload["location_longitude"]) if payload["location_longitude"] is not None else None,
        location_accuracy_meters=(
            float(payload["location_accuracy_meters"]) if payload["location_accuracy_meters"] is not None else None
        ),
        requested_field_code=payload["requested_field_code"],
        created_at=str(payload["binding_created_at"]),
        updated_at=str(payload["binding_updated_at"]),
        deactivated_at=payload["deactivated_at"],
    )
    field = FieldRegistryField(
        id=str(payload["field_id_row"]),
        field_registry_version_id=str(payload["field_registry_version_id_row"]),
        project_id=str(payload["field_project_id"]),
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
    return ParticipantFieldBindingRecord(binding=binding, field=field, boundary=boundary)
