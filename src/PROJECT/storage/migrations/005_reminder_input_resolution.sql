CREATE TABLE IF NOT EXISTS reminder_deliveries (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  field_season_id TEXT,
  seasonal_event_id TEXT,
  input_resolution_session_id TEXT,
  provider_user_id TEXT NOT NULL,
  chat_id INTEGER NOT NULL,
  reminder_type_code TEXT NOT NULL,
  reminder_status_code TEXT NOT NULL DEFAULT 'pending',
  resume_token TEXT NOT NULL UNIQUE,
  resume_target_code TEXT NOT NULL,
  message_text TEXT NOT NULL,
  due_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  sent_at TEXT,
  completed_at TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (field_season_id) REFERENCES field_seasons(id),
  FOREIGN KEY (seasonal_event_id) REFERENCES seasonal_events(id),
  FOREIGN KEY (input_resolution_session_id) REFERENCES input_resolution_sessions(id)
);

CREATE TABLE IF NOT EXISTS input_resolution_sessions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  chat_id INTEGER NOT NULL,
  target_type_code TEXT,
  method_code TEXT,
  session_status_code TEXT NOT NULL,
  current_step_code TEXT NOT NULL,
  raw_input_text TEXT,
  selected_candidate_id TEXT,
  resolved_value_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  resolved_at TEXT,
  escalated_at TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id)
);

CREATE TABLE IF NOT EXISTS input_resolution_attempts (
  id TEXT PRIMARY KEY,
  input_resolution_session_id TEXT NOT NULL,
  method_code TEXT NOT NULL,
  raw_input_text TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (input_resolution_session_id) REFERENCES input_resolution_sessions(id)
);

CREATE TABLE IF NOT EXISTS input_resolution_candidates (
  id TEXT PRIMARY KEY,
  input_resolution_session_id TEXT NOT NULL,
  input_resolution_attempt_id TEXT NOT NULL,
  candidate_rank INTEGER NOT NULL,
  candidate_type_code TEXT NOT NULL,
  raw_value TEXT NOT NULL,
  normalized_value_json TEXT NOT NULL DEFAULT '{}',
  confidence_score REAL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (input_resolution_session_id) REFERENCES input_resolution_sessions(id),
  FOREIGN KEY (input_resolution_attempt_id) REFERENCES input_resolution_attempts(id)
);

CREATE TABLE IF NOT EXISTS input_resolution_decisions (
  id TEXT PRIMARY KEY,
  input_resolution_session_id TEXT NOT NULL,
  selected_candidate_id TEXT,
  decision_code TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (input_resolution_session_id) REFERENCES input_resolution_sessions(id),
  FOREIGN KEY (selected_candidate_id) REFERENCES input_resolution_candidates(id)
);

CREATE INDEX IF NOT EXISTS idx_reminder_deliveries_status_due
ON reminder_deliveries(reminder_status_code, due_at);

CREATE INDEX IF NOT EXISTS idx_reminder_deliveries_resume_token
ON reminder_deliveries(resume_token);

CREATE INDEX IF NOT EXISTS idx_input_resolution_sessions_status_updated
ON input_resolution_sessions(session_status_code, updated_at);

CREATE INDEX IF NOT EXISTS idx_input_resolution_sessions_participant
ON input_resolution_sessions(participant_id, created_at);

CREATE INDEX IF NOT EXISTS idx_input_resolution_attempts_session
ON input_resolution_attempts(input_resolution_session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_input_resolution_candidates_session_rank
ON input_resolution_candidates(input_resolution_session_id, candidate_rank);

CREATE INDEX IF NOT EXISTS idx_input_resolution_decisions_session
ON input_resolution_decisions(input_resolution_session_id, created_at);
