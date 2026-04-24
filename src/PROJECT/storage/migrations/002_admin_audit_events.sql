CREATE TABLE IF NOT EXISTS admin_audit_events (
  id TEXT PRIMARY KEY,
  actor_type_code TEXT NOT NULL,
  actor_id TEXT,
  action_code TEXT NOT NULL,
  target_type_code TEXT,
  target_id TEXT,
  result_code TEXT NOT NULL,
  source_code TEXT NOT NULL,
  request_path TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  occurred_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_events_action_time
ON admin_audit_events(action_code, occurred_at);

CREATE INDEX IF NOT EXISTS idx_admin_audit_events_actor_time
ON admin_audit_events(actor_type_code, actor_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_admin_audit_events_target
ON admin_audit_events(target_type_code, target_id);
