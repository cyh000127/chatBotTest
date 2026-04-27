import pytest

from PROJECT.settings import SqliteSettings
from PROJECT.storage.fields import (
    FIELD_REGISTRY_STATUS_ARCHIVED,
    FIELD_REGISTRY_STATUS_DRAFT,
    FIELD_REGISTRY_STATUS_PUBLISHED,
    SqliteFieldRegistryRepository,
)
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def _repository(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    return runtime, SqliteFieldRegistryRepository(runtime.connection)


def test_field_registry_repository_imports_polygon_and_reloads_boundary(tmp_path):
    runtime, repository = _repository(tmp_path)

    try:
        version = repository.create_registry_version(version_label="v1")
        record = repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[
                (37.0, 127.0),
                (37.0, 127.1),
                (37.1, 127.1),
                (37.1, 127.0),
            ],
            area_square_meters=1234.5,
            metadata={"source": "test"},
        )

        assert version.version_status_code == FIELD_REGISTRY_STATUS_DRAFT
        assert record.field.field_code == "FIELD-001"
        assert record.field.display_name == "논 1"
        assert record.polygon[0] == record.polygon[-1]
        assert record.bbox["min_latitude"] == pytest.approx(37.0)
        assert record.bbox["max_longitude"] == pytest.approx(127.1)
        assert record.boundary.centroid_latitude == pytest.approx(37.05)
        assert record.boundary.centroid_longitude == pytest.approx(127.05)
        loaded = repository.list_fields_for_version(version.id)
        assert [item.field.field_code for item in loaded] == ["FIELD-001"]
    finally:
        runtime.close()


def test_field_registry_repository_publish_archives_previous_version(tmp_path):
    runtime, repository = _repository(tmp_path)

    try:
        first = repository.create_registry_version(version_label="v1")
        second = repository.create_registry_version(version_label="v2")

        repository.import_field(
            field_registry_version_id=first.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[
                (37.0, 127.0),
                (37.0, 127.1),
                (37.1, 127.1),
                (37.1, 127.0),
            ],
        )
        repository.import_field(
            field_registry_version_id=second.id,
            field_code="FIELD-002",
            display_name="논 2",
            polygon=[
                (36.9, 127.0),
                (36.9, 127.1),
                (37.0, 127.1),
                (37.0, 127.0),
            ],
        )

        first_published = repository.publish_version(first.id)
        second_published = repository.publish_version(second.id)

        assert first_published.version_status_code == FIELD_REGISTRY_STATUS_PUBLISHED
        latest = repository.latest_published_version()
        assert latest is not None
        assert latest.id == second.id
        assert latest.version_status_code == FIELD_REGISTRY_STATUS_PUBLISHED
        reloaded_first = repository.get_registry_version(first.id)
        assert reloaded_first is not None
        assert reloaded_first.version_status_code == FIELD_REGISTRY_STATUS_ARCHIVED
        published_field = repository.get_published_field_by_code(field_code="FIELD-002")
        assert published_field is not None
        assert published_field.field.display_name == "논 2"
    finally:
        runtime.close()


def test_field_registry_repository_rejects_invalid_polygon(tmp_path):
    runtime, repository = _repository(tmp_path)

    try:
        version = repository.create_registry_version(version_label="v1")
        with pytest.raises(ValueError):
            repository.import_field(
                field_registry_version_id=version.id,
                field_code="FIELD-INVALID",
                display_name="잘못된 농지",
                polygon=[(37.0, 127.0), (37.0, 127.0)],
            )
    finally:
        runtime.close()
