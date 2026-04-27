from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

from PROJECT.fields.geometry import point_in_polygon
from PROJECT.storage.fields import FieldRegistryFieldRecord, SqliteFieldRegistryRepository
from PROJECT.storage.invitations import DEFAULT_LOCAL_PROJECT_ID


@dataclass(frozen=True)
class FieldCandidate:
    field_id: str
    field_code: str
    display_name: str
    field_registry_version_id: str
    centroid_distance_meters: float


@dataclass(frozen=True)
class FieldLookupResult:
    version_id: str | None
    candidates: tuple[FieldCandidate, ...]


class FieldLookupService:
    def __init__(self, repository: SqliteFieldRegistryRepository) -> None:
        self._repository = repository

    def find_location_candidates(
        self,
        *,
        latitude: float,
        longitude: float,
        project_id: str = DEFAULT_LOCAL_PROJECT_ID,
    ) -> FieldLookupResult:
        version = self._repository.latest_published_version(project_id=project_id)
        if version is None:
            return FieldLookupResult(version_id=None, candidates=())
        records = self._repository.list_fields_for_version(version.id)
        candidates: list[FieldCandidate] = []
        for record in records:
            bbox = record.bbox
            if latitude < bbox["min_latitude"] or latitude > bbox["max_latitude"]:
                continue
            if longitude < bbox["min_longitude"] or longitude > bbox["max_longitude"]:
                continue
            if not point_in_polygon(latitude, longitude, record.polygon):
                continue
            candidates.append(
                FieldCandidate(
                    field_id=record.field.id,
                    field_code=record.field.field_code,
                    display_name=record.field.display_name,
                    field_registry_version_id=record.field.field_registry_version_id,
                    centroid_distance_meters=_haversine_distance_meters(
                        latitude,
                        longitude,
                        record.boundary.centroid_latitude,
                        record.boundary.centroid_longitude,
                    ),
                )
            )
        candidates.sort(key=lambda item: (item.centroid_distance_meters, item.field_code))
        return FieldLookupResult(version_id=version.id, candidates=tuple(candidates))

    def find_field_by_code(
        self,
        *,
        field_code: str,
        project_id: str = DEFAULT_LOCAL_PROJECT_ID,
    ) -> FieldRegistryFieldRecord | None:
        return self._repository.get_published_field_by_code(field_code=field_code, project_id=project_id)


def _haversine_distance_meters(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    radius = 6_371_000.0
    lat1 = radians(latitude_a)
    lat2 = radians(latitude_b)
    delta_lat = radians(latitude_b - latitude_a)
    delta_lng = radians(longitude_b - longitude_a)
    hav = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
    return 2 * radius * asin(sqrt(hav))
