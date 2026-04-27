from PROJECT.fields.lookup import FieldLookupService
from PROJECT.settings import SqliteSettings
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def _service(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    repository = SqliteFieldRegistryRepository(runtime.connection)
    return runtime, repository, FieldLookupService(repository)


def test_field_lookup_service_returns_only_published_polygon_matches(tmp_path):
    runtime, repository, service = _service(tmp_path)

    try:
        published = repository.create_registry_version(version_label="v1")
        repository.import_field(
            field_registry_version_id=published.id,
            field_code="FIELD-PUBLISHED",
            display_name="공개 농지",
            polygon=[
                (37.0, 127.0),
                (37.0, 127.1),
                (37.1, 127.1),
                (37.1, 127.0),
            ],
        )
        repository.publish_version(published.id)

        draft = repository.create_registry_version(version_label="v2")
        repository.import_field(
            field_registry_version_id=draft.id,
            field_code="FIELD-DRAFT",
            display_name="초안 농지",
            polygon=[
                (37.0, 127.0),
                (37.0, 127.1),
                (37.1, 127.1),
                (37.1, 127.0),
            ],
        )

        result = service.find_location_candidates(latitude=37.05, longitude=127.05)

        assert result.version_id == published.id
        assert [candidate.field_code for candidate in result.candidates] == ["FIELD-PUBLISHED"]
    finally:
        runtime.close()


def test_field_lookup_service_returns_multiple_candidates_sorted_by_centroid_distance(tmp_path):
    runtime, repository, service = _service(tmp_path)

    try:
        version = repository.create_registry_version(version_label="v1")
        repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-NEAR",
            display_name="가까운 농지",
            polygon=[
                (37.0, 127.0),
                (37.0, 127.08),
                (37.08, 127.08),
                (37.08, 127.0),
            ],
        )
        repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-FAR",
            display_name="겹치는 농지",
            polygon=[
                (36.98, 126.98),
                (36.98, 127.12),
                (37.12, 127.12),
                (37.12, 126.98),
            ],
        )
        repository.publish_version(version.id)

        result = service.find_location_candidates(latitude=37.04, longitude=127.04)

        assert [candidate.field_code for candidate in result.candidates] == ["FIELD-NEAR", "FIELD-FAR"]
        assert result.candidates[0].centroid_distance_meters <= result.candidates[1].centroid_distance_meters
    finally:
        runtime.close()


def test_field_lookup_service_can_find_field_by_code_from_latest_published_version(tmp_path):
    runtime, repository, service = _service(tmp_path)

    try:
        first = repository.create_registry_version(version_label="v1")
        repository.import_field(
            field_registry_version_id=first.id,
            field_code="FIELD-001",
            display_name="이전 농지",
            polygon=[
                (37.0, 127.0),
                (37.0, 127.1),
                (37.1, 127.1),
                (37.1, 127.0),
            ],
        )
        repository.publish_version(first.id)

        second = repository.create_registry_version(version_label="v2")
        repository.import_field(
            field_registry_version_id=second.id,
            field_code="FIELD-001",
            display_name="최신 농지",
            polygon=[
                (36.9, 127.0),
                (36.9, 127.1),
                (37.0, 127.1),
                (37.0, 127.0),
            ],
        )
        repository.publish_version(second.id)

        found = service.find_field_by_code(field_code="FIELD-001")

        assert found is not None
        assert found.field.display_name == "최신 농지"
        assert found.field.field_registry_version_id == second.id
    finally:
        runtime.close()
