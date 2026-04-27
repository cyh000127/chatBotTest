from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from PROJECT.storage.invitations import utc_now_text

PROJECT_SEASON_STATUS_OPEN = "open"
FIELD_SEASON_STATUS_OPEN = "open"
SEASONAL_EVENT_STATUS_RECORDED = "recorded"
SEASONAL_EVENT_TYPE_FERTILIZER_INPUT = "fertilizer_input_confirmed"
SEASONAL_EVENT_TYPE_YIELD_INPUT = "yield_input_confirmed"
ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM = "chat_confirm"


@dataclass(frozen=True)
class ProjectSeason:
    id: str
    project_id: str
    season_year: int
    season_label: str
    season_status_code: str
    season_start_date: str | None
    season_end_date: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FieldSeason:
    id: str
    project_season_id: str
    participant_id: str
    field_binding_id: str
    field_id: str
    field_season_status_code: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SeasonalEvent:
    id: str
    project_id: str
    participant_id: str
    field_season_id: str | None
    field_binding_id: str | None
    field_id: str | None
    event_type_code: str
    event_status_code: str
    input_source_code: str
    occurred_on: str
    payload_json: str
    created_at: str
    updated_at: str

    @property
    def payload(self) -> dict:
        parsed = json.loads(self.payload_json)
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class FertilizerApplicationRecord:
    id: str
    project_id: str
    participant_id: str
    field_season_id: str | None
    seasonal_event_id: str
    field_binding_id: str | None
    field_id: str | None
    input_source_code: str
    used_flag: int
    fertilizer_kind_code: str | None
    product_name: str | None
    amount_value: float | None
    amount_unit: str | None
    applied_date: str
    payload_json: str
    created_at: str
    updated_at: str

    @property
    def payload(self) -> dict:
        parsed = json.loads(self.payload_json)
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class YieldRecord:
    id: str
    project_id: str
    participant_id: str
    field_season_id: str | None
    seasonal_event_id: str
    field_binding_id: str | None
    field_id: str | None
    input_source_code: str
    ready_flag: int
    field_name: str | None
    amount_value: float | None
    amount_unit: str | None
    harvest_date: str
    payload_json: str
    created_at: str
    updated_at: str

    @property
    def payload(self) -> dict:
        parsed = json.loads(self.payload_json)
        return parsed if isinstance(parsed, dict) else {}


class SqliteSeasonActivityRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def ensure_project_season(self, *, project_id: str, season_year: int) -> ProjectSeason:
        with self._lock:
            existing = self.get_project_season(project_id=project_id, season_year=season_year)
            if existing is not None:
                return existing
            now = utc_now_text()
            project_season_id = f"project_season_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO project_seasons (
                  id,
                  project_id,
                  season_year,
                  season_label,
                  season_status_code,
                  season_start_date,
                  season_end_date,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_season_id,
                    project_id,
                    season_year,
                    f"{season_year}",
                    PROJECT_SEASON_STATUS_OPEN,
                    f"{season_year:04d}-01-01",
                    f"{season_year:04d}-12-31",
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_project_season(project_id=project_id, season_year=season_year)
            if created is None:
                raise RuntimeError("생성한 project season을 다시 읽을 수 없습니다.")
            return created

    def get_project_season(self, *, project_id: str, season_year: int) -> ProjectSeason | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM project_seasons
            WHERE project_id = ?
              AND season_year = ?
            LIMIT 1
            """,
            (project_id, season_year),
        ).fetchone()
        if row is None:
            return None
        return ProjectSeason(**dict(row))

    def ensure_field_season(
        self,
        *,
        project_season_id: str,
        participant_id: str,
        field_binding_id: str,
        field_id: str,
    ) -> FieldSeason:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT *
                FROM field_seasons
                WHERE project_season_id = ?
                  AND field_binding_id = ?
                LIMIT 1
                """,
                (project_season_id, field_binding_id),
            ).fetchone()
            if row is not None:
                return FieldSeason(**dict(row))

            now = utc_now_text()
            field_season_id = f"field_season_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO field_seasons (
                  id,
                  project_season_id,
                  participant_id,
                  field_binding_id,
                  field_id,
                  field_season_status_code,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    field_season_id,
                    project_season_id,
                    participant_id,
                    field_binding_id,
                    field_id,
                    FIELD_SEASON_STATUS_OPEN,
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_field_season(field_season_id)
            if created is None:
                raise RuntimeError("생성한 field season을 다시 읽을 수 없습니다.")
            return created

    def get_field_season(self, field_season_id: str) -> FieldSeason | None:
        row = self._connection.execute(
            "SELECT * FROM field_seasons WHERE id = ?",
            (field_season_id,),
        ).fetchone()
        if row is None:
            return None
        return FieldSeason(**dict(row))

    def create_seasonal_event(
        self,
        *,
        project_id: str,
        participant_id: str,
        event_type_code: str,
        occurred_on: str,
        input_source_code: str = ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM,
        field_season_id: str | None = None,
        field_binding_id: str | None = None,
        field_id: str | None = None,
        payload: dict | None = None,
    ) -> SeasonalEvent:
        with self._lock:
            now = utc_now_text()
            seasonal_event_id = f"seasonal_event_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO seasonal_events (
                  id,
                  project_id,
                  participant_id,
                  field_season_id,
                  field_binding_id,
                  field_id,
                  event_type_code,
                  event_status_code,
                  input_source_code,
                  occurred_on,
                  payload_json,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    seasonal_event_id,
                    project_id,
                    participant_id,
                    field_season_id,
                    field_binding_id,
                    field_id,
                    event_type_code,
                    SEASONAL_EVENT_STATUS_RECORDED,
                    input_source_code,
                    occurred_on,
                    json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_seasonal_event(seasonal_event_id)
            if created is None:
                raise RuntimeError("생성한 seasonal event를 다시 읽을 수 없습니다.")
            return created

    def get_seasonal_event(self, seasonal_event_id: str) -> SeasonalEvent | None:
        row = self._connection.execute(
            "SELECT * FROM seasonal_events WHERE id = ?",
            (seasonal_event_id,),
        ).fetchone()
        if row is None:
            return None
        return SeasonalEvent(**dict(row))

    def create_fertilizer_record(
        self,
        *,
        project_id: str,
        participant_id: str,
        seasonal_event_id: str,
        used_flag: bool,
        fertilizer_kind_code: str | None,
        product_name: str | None,
        amount_value: float | None,
        amount_unit: str | None,
        applied_date: str,
        input_source_code: str = ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM,
        field_season_id: str | None = None,
        field_binding_id: str | None = None,
        field_id: str | None = None,
        payload: dict | None = None,
    ) -> FertilizerApplicationRecord:
        with self._lock:
            now = utc_now_text()
            record_id = f"fertilizer_record_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO fertilizer_application_records (
                  id,
                  project_id,
                  participant_id,
                  field_season_id,
                  seasonal_event_id,
                  field_binding_id,
                  field_id,
                  input_source_code,
                  used_flag,
                  fertilizer_kind_code,
                  product_name,
                  amount_value,
                  amount_unit,
                  applied_date,
                  payload_json,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    project_id,
                    participant_id,
                    field_season_id,
                    seasonal_event_id,
                    field_binding_id,
                    field_id,
                    input_source_code,
                    1 if used_flag else 0,
                    fertilizer_kind_code,
                    product_name,
                    amount_value,
                    amount_unit,
                    applied_date,
                    json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_fertilizer_record(record_id)
            if created is None:
                raise RuntimeError("생성한 fertilizer record를 다시 읽을 수 없습니다.")
            return created

    def get_fertilizer_record(self, record_id: str) -> FertilizerApplicationRecord | None:
        row = self._connection.execute(
            "SELECT * FROM fertilizer_application_records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return FertilizerApplicationRecord(**dict(row))

    def list_fertilizer_records(self, *, participant_id: str | None = None) -> tuple[FertilizerApplicationRecord, ...]:
        if participant_id is None:
            rows = self._connection.execute(
                "SELECT * FROM fertilizer_application_records ORDER BY created_at ASC"
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT *
                FROM fertilizer_application_records
                WHERE participant_id = ?
                ORDER BY created_at ASC
                """,
                (participant_id,),
            ).fetchall()
        return tuple(FertilizerApplicationRecord(**dict(row)) for row in rows)

    def create_yield_record(
        self,
        *,
        project_id: str,
        participant_id: str,
        seasonal_event_id: str,
        ready_flag: bool,
        field_name: str | None,
        amount_value: float | None,
        amount_unit: str | None,
        harvest_date: str,
        input_source_code: str = ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM,
        field_season_id: str | None = None,
        field_binding_id: str | None = None,
        field_id: str | None = None,
        payload: dict | None = None,
    ) -> YieldRecord:
        with self._lock:
            now = utc_now_text()
            record_id = f"yield_record_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO yield_records (
                  id,
                  project_id,
                  participant_id,
                  field_season_id,
                  seasonal_event_id,
                  field_binding_id,
                  field_id,
                  input_source_code,
                  ready_flag,
                  field_name,
                  amount_value,
                  amount_unit,
                  harvest_date,
                  payload_json,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    project_id,
                    participant_id,
                    field_season_id,
                    seasonal_event_id,
                    field_binding_id,
                    field_id,
                    input_source_code,
                    1 if ready_flag else 0,
                    field_name,
                    amount_value,
                    amount_unit,
                    harvest_date,
                    json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_yield_record(record_id)
            if created is None:
                raise RuntimeError("생성한 yield record를 다시 읽을 수 없습니다.")
            return created

    def get_yield_record(self, record_id: str) -> YieldRecord | None:
        row = self._connection.execute(
            "SELECT * FROM yield_records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return YieldRecord(**dict(row))

    def list_yield_records(self, *, participant_id: str | None = None) -> tuple[YieldRecord, ...]:
        if participant_id is None:
            rows = self._connection.execute(
                "SELECT * FROM yield_records ORDER BY created_at ASC"
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT *
                FROM yield_records
                WHERE participant_id = ?
                ORDER BY created_at ASC
                """,
                (participant_id,),
            ).fetchall()
        return tuple(YieldRecord(**dict(row)) for row in rows)
