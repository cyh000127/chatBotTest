CREATE TABLE IF NOT EXISTS evidence_request_events (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  seasonal_event_id TEXT,
  field_binding_id TEXT,
  field_id TEXT,
  request_type_code TEXT NOT NULL,
  request_status_code TEXT NOT NULL DEFAULT 'open',
  request_reason_code TEXT,
  requested_via_code TEXT NOT NULL DEFAULT 'runtime',
  due_at TEXT,
  satisfied_at TEXT,
  cancelled_at TEXT,
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

CREATE TABLE IF NOT EXISTS evidence_submission_sessions (
  id TEXT PRIMARY KEY,
  evidence_request_event_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  chat_id INTEGER NOT NULL,
  field_season_id TEXT,
  field_binding_id TEXT,
  field_id TEXT,
  session_status_code TEXT NOT NULL,
  current_step_code TEXT NOT NULL,
  accepted_location_latitude REAL,
  accepted_location_longitude REAL,
  accepted_location_accuracy_meters REAL,
  accepted_location_recorded_at TEXT,
  draft_payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  abandoned_at TEXT,
  FOREIGN KEY (evidence_request_event_id) REFERENCES evidence_request_events(id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);

CREATE TABLE IF NOT EXISTS evidence_submissions (
  id TEXT PRIMARY KEY,
  evidence_submission_session_id TEXT NOT NULL,
  evidence_request_event_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  field_binding_id TEXT,
  field_id TEXT,
  provider_message_id TEXT,
  provider_file_id TEXT,
  provider_file_unique_id TEXT,
  file_name TEXT,
  mime_type TEXT,
  file_size_bytes INTEGER,
  artifact_status_code TEXT NOT NULL,
  staged_artifact_uri TEXT,
  checksum_sha256 TEXT,
  captured_at TEXT,
  uploaded_at TEXT NOT NULL,
  submitted_at TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (evidence_submission_session_id) REFERENCES evidence_submission_sessions(id),
  FOREIGN KEY (evidence_request_event_id) REFERENCES evidence_request_events(id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (field_binding_id) REFERENCES participant_field_bindings(id),
  FOREIGN KEY (field_id) REFERENCES field_registry_fields(id)
);

CREATE TABLE IF NOT EXISTS evidence_validation_signals (
  id TEXT PRIMARY KEY,
  evidence_submission_id TEXT NOT NULL,
  signal_type_code TEXT NOT NULL,
  signal_status_code TEXT NOT NULL,
  numeric_value REAL,
  text_value TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY (evidence_submission_id) REFERENCES evidence_submissions(id)
);

CREATE TABLE IF NOT EXISTS evidence_validation_state_logs (
  id TEXT PRIMARY KEY,
  evidence_submission_id TEXT NOT NULL,
  from_state_code TEXT,
  to_state_code TEXT NOT NULL,
  reason_code TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY (evidence_submission_id) REFERENCES evidence_submissions(id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_request_events_participant_due
ON evidence_request_events(participant_id, request_status_code, due_at);

CREATE INDEX IF NOT EXISTS idx_evidence_request_events_seasonal_event
ON evidence_request_events(seasonal_event_id, request_type_code);

CREATE INDEX IF NOT EXISTS idx_evidence_submission_sessions_status_updated
ON evidence_submission_sessions(session_status_code, updated_at);

CREATE INDEX IF NOT EXISTS idx_evidence_submission_sessions_request
ON evidence_submission_sessions(evidence_request_event_id, created_at);

CREATE INDEX IF NOT EXISTS idx_evidence_submissions_session_submitted
ON evidence_submissions(evidence_submission_session_id, submitted_at);

CREATE INDEX IF NOT EXISTS idx_evidence_submissions_status_uploaded
ON evidence_submissions(artifact_status_code, uploaded_at);

CREATE INDEX IF NOT EXISTS idx_evidence_validation_signals_submission_type
ON evidence_validation_signals(evidence_submission_id, signal_type_code);

CREATE INDEX IF NOT EXISTS idx_evidence_validation_state_logs_submission_created
ON evidence_validation_state_logs(evidence_submission_id, created_at);
