CREATE TABLE IF NOT EXISTS project_seasons (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  season_year INTEGER NOT NULL,
  season_label TEXT NOT NULL,
  season_status_code TEXT NOT NULL DEFAULT 'open',
  season_start_date TEXT,
  season_end_date TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  UNIQUE(project_id, season_year)
);

CREATE TABLE IF NOT EXISTS field_seasons (
  id TEXT PRIMARY KEY,
  project_season_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_binding_id TEXT NOT NULL,
  field_id TEXT NOT NULL,
  field_season_status_code TEXT NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_season_id) REFERENCES project_seasons(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id),
  UNIQUE(project_season_id, field_binding_id)
);

CREATE TABLE IF NOT EXISTS seasonal_events (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  field_binding_id TEXT,
  field_id TEXT,
  event_type_code TEXT NOT NULL,
  event_status_code TEXT NOT NULL,
  input_source_code TEXT NOT NULL,
  occurred_on TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);

CREATE TABLE IF NOT EXISTS fertilizer_application_records (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  seasonal_event_id TEXT NOT NULL,
  field_binding_id TEXT,
  field_id TEXT,
  input_source_code TEXT NOT NULL,
  used_flag INTEGER NOT NULL,
  fertilizer_kind_code TEXT,
  product_name TEXT,
  amount_value REAL,
  amount_unit TEXT,
  applied_date TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (seasonal_event_id) REFERENCES seasonal_events(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);

CREATE TABLE IF NOT EXISTS yield_records (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  seasonal_event_id TEXT NOT NULL,
  field_binding_id TEXT,
  field_id TEXT,
  input_source_code TEXT NOT NULL,
  ready_flag INTEGER NOT NULL,
  field_name TEXT,
  amount_value REAL,
  amount_unit TEXT,
  harvest_date TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (seasonal_event_id) REFERENCES seasonal_events(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);

CREATE INDEX IF NOT EXISTS idx_project_seasons_project_year
ON project_seasons(project_id, season_year);

CREATE INDEX IF NOT EXISTS idx_field_seasons_project_binding
ON field_seasons(project_season_id, field_binding_id);

CREATE INDEX IF NOT EXISTS idx_seasonal_events_participant_date
ON seasonal_events(participant_id, occurred_on);

CREATE INDEX IF NOT EXISTS idx_seasonal_events_field_season
ON seasonal_events(field_season_id, occurred_on);

CREATE INDEX IF NOT EXISTS idx_fertilizer_records_participant_date
ON fertilizer_application_records(participant_id, applied_date);

CREATE INDEX IF NOT EXISTS idx_yield_records_participant_date
ON yield_records(participant_id, harvest_date);
