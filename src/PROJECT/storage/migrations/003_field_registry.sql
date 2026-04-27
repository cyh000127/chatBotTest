CREATE TABLE IF NOT EXISTS field_registry_versions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  version_label TEXT NOT NULL,
  source_code TEXT NOT NULL DEFAULT 'local_runtime',
  version_status_code TEXT NOT NULL,
  published_at TEXT,
  archived_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(project_id, version_label)
);

CREATE TABLE IF NOT EXISTS field_registry_fields (
  id TEXT PRIMARY KEY,
  field_registry_version_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  field_code TEXT NOT NULL,
  display_name TEXT NOT NULL,
  area_square_meters REAL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (field_registry_version_id) REFERENCES field_registry_versions(id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(field_registry_version_id, field_code)
);

CREATE TABLE IF NOT EXISTS field_registry_boundaries (
  id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL,
  polygon_json TEXT NOT NULL,
  bounding_box_json TEXT NOT NULL,
  centroid_latitude REAL NOT NULL,
  centroid_longitude REAL NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);

CREATE TABLE IF NOT EXISTS participant_field_bindings (
  id TEXT PRIMARY KEY,
  participant_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  field_id TEXT NOT NULL,
  field_registry_version_id TEXT NOT NULL,
  binding_status_code TEXT NOT NULL,
  binding_source_code TEXT NOT NULL,
  onboarding_session_id TEXT,
  provider_user_id TEXT,
  chat_id INTEGER,
  location_latitude REAL,
  location_longitude REAL,
  location_accuracy_meters REAL,
  requested_field_code TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deactivated_at TEXT,
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id),
  FOREIGN KEY (field_registry_version_id) REFERENCES field_registry_versions(id),
  FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id)
);

CREATE TABLE IF NOT EXISTS field_binding_exceptions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT,
  onboarding_session_id TEXT,
  provider_user_id TEXT,
  chat_id INTEGER,
  field_registry_version_id TEXT,
  exception_type_code TEXT NOT NULL,
  exception_status_code TEXT NOT NULL DEFAULT 'open',
  route_hint TEXT NOT NULL DEFAULT 'manual_resolution_required',
  requested_field_code TEXT,
  location_latitude REAL,
  location_longitude REAL,
  location_accuracy_meters REAL,
  candidate_field_ids_json TEXT NOT NULL DEFAULT '[]',
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  resolved_at TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id),
  FOREIGN KEY (field_registry_version_id) REFERENCES field_registry_versions(id)
);

CREATE INDEX IF NOT EXISTS idx_field_registry_versions_project_status
ON field_registry_versions(project_id, version_status_code, published_at);

CREATE INDEX IF NOT EXISTS idx_field_registry_fields_version_code
ON field_registry_fields(field_registry_version_id, field_code);

CREATE INDEX IF NOT EXISTS idx_participant_field_bindings_participant_status
ON participant_field_bindings(participant_id, binding_status_code, created_at);

CREATE INDEX IF NOT EXISTS idx_participant_field_bindings_field_status
ON participant_field_bindings(field_id, binding_status_code, created_at);

CREATE INDEX IF NOT EXISTS idx_field_binding_exceptions_status_created
ON field_binding_exceptions(exception_status_code, created_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_participant_field_bindings_active_participant_field
ON participant_field_bindings(participant_id, field_id)
WHERE binding_status_code = 'active';

CREATE UNIQUE INDEX IF NOT EXISTS idx_participant_field_bindings_active_field
ON participant_field_bindings(field_id)
WHERE binding_status_code = 'active';
