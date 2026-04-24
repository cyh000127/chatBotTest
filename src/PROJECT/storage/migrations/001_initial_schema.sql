CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_users (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  project_name TEXT NOT NULL,
  project_status_code TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS participants (
  id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  preferred_language TEXT NOT NULL,
  participant_status_code TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS participant_private_contacts (
  id TEXT PRIMARY KEY,
  participant_id TEXT NOT NULL,
  contact_type_code TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  raw_value TEXT NOT NULL,
  is_primary INTEGER NOT NULL DEFAULT 1,
  verified_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (participant_id) REFERENCES participants(id)
);

CREATE TABLE IF NOT EXISTS participant_identities (
  id TEXT PRIMARY KEY,
  participant_id TEXT,
  identity_provider_code TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  provider_handle TEXT,
  linked_contact_id TEXT,
  link_provenance TEXT NOT NULL,
  is_primary INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(identity_provider_code, provider_user_id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (linked_contact_id) REFERENCES participant_private_contacts(id)
);

CREATE TABLE IF NOT EXISTS project_invitations (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  channel_code TEXT NOT NULL DEFAULT 'telegram',
  invite_code TEXT NOT NULL UNIQUE,
  invite_token_hash TEXT,
  invite_status_code TEXT NOT NULL,
  target_contact_type_code TEXT,
  target_contact_normalized TEXT,
  target_contact_raw TEXT,
  target_participant_role_code TEXT NOT NULL DEFAULT 'farmer',
  invited_by_admin_user_id TEXT,
  issued_at TEXT NOT NULL,
  expires_at TEXT,
  used_at TEXT,
  revoked_at TEXT,
  accepted_participant_id TEXT,
  accepted_enrollment_id TEXT,
  used_channel_message_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (invited_by_admin_user_id) REFERENCES admin_users(id),
  FOREIGN KEY (accepted_participant_id) REFERENCES participants(id),
  FOREIGN KEY (accepted_enrollment_id) REFERENCES project_enrollments(id),
  FOREIGN KEY (used_channel_message_id) REFERENCES channel_messages(id)
);

CREATE TABLE IF NOT EXISTS onboarding_sessions (
  id TEXT PRIMARY KEY,
  channel_code TEXT NOT NULL DEFAULT 'telegram',
  identity_provider_code TEXT NOT NULL DEFAULT 'telegram',
  provider_user_id TEXT NOT NULL,
  provider_handle TEXT,
  participant_identity_id TEXT,
  participant_id TEXT,
  project_invitation_id TEXT,
  project_id TEXT,
  session_status_code TEXT NOT NULL,
  current_step_code TEXT NOT NULL,
  preferred_locale_code TEXT NOT NULL DEFAULT 'ko',
  draft_payload_json TEXT NOT NULL DEFAULT '{}',
  last_inbound_channel_message_id TEXT,
  last_outbound_channel_message_id TEXT,
  started_at TEXT NOT NULL,
  last_interaction_at TEXT NOT NULL,
  expires_at TEXT,
  submitted_at TEXT,
  completed_at TEXT,
  abandoned_at TEXT,
  result_participant_id TEXT,
  result_enrollment_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (participant_identity_id) REFERENCES participant_identities(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (project_invitation_id) REFERENCES project_invitations(id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (last_inbound_channel_message_id) REFERENCES channel_messages(id),
  FOREIGN KEY (last_outbound_channel_message_id) REFERENCES channel_messages(id),
  FOREIGN KEY (result_participant_id) REFERENCES participants(id),
  FOREIGN KEY (result_enrollment_id) REFERENCES project_enrollments(id)
);

CREATE TABLE IF NOT EXISTS onboarding_session_events (
  id TEXT PRIMARY KEY,
  onboarding_session_id TEXT NOT NULL,
  event_type_code TEXT NOT NULL,
  from_step_code TEXT,
  to_step_code TEXT,
  from_status_code TEXT,
  to_status_code TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  channel_message_id TEXT,
  acted_by_type TEXT NOT NULL,
  acted_by_id TEXT,
  occurred_at TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id),
  FOREIGN KEY (channel_message_id) REFERENCES channel_messages(id)
);

CREATE TABLE IF NOT EXISTS project_enrollments (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  participant_id TEXT NOT NULL,
  invitation_id TEXT,
  participant_role_code TEXT NOT NULL DEFAULT 'farmer',
  enrollment_status_code TEXT NOT NULL,
  enrollment_source_code TEXT NOT NULL,
  accepted_at TEXT,
  activated_at TEXT,
  activated_by_admin_user_id TEXT,
  revoked_at TEXT,
  revoked_by_admin_user_id TEXT,
  rejection_reason_code TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (invitation_id) REFERENCES project_invitations(id),
  FOREIGN KEY (activated_by_admin_user_id) REFERENCES admin_users(id),
  FOREIGN KEY (revoked_by_admin_user_id) REFERENCES admin_users(id)
);

CREATE TABLE IF NOT EXISTS channel_messages (
  id TEXT PRIMARY KEY,
  channel_code TEXT NOT NULL DEFAULT 'telegram',
  direction_code TEXT NOT NULL,
  provider_message_id TEXT,
  participant_identity_id TEXT,
  project_id TEXT,
  provider_user_id TEXT,
  chat_id INTEGER NOT NULL,
  canonical_intent_code TEXT,
  message_type_code TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  occurred_at TEXT NOT NULL,
  FOREIGN KEY (participant_identity_id) REFERENCES participant_identities(id),
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS message_deliveries (
  id TEXT PRIMARY KEY,
  channel_message_id TEXT NOT NULL,
  delivery_state_code TEXT NOT NULL,
  provider_status TEXT,
  delivered_at TEXT,
  failed_at TEXT,
  failure_reason_code TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (channel_message_id) REFERENCES channel_messages(id)
);

CREATE TABLE IF NOT EXISTS admin_follow_up_queue (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  participant_id TEXT,
  field_id TEXT,
  field_season_id TEXT,
  seasonal_event_id TEXT,
  evidence_request_event_id TEXT,
  input_resolution_session_id TEXT,
  onboarding_session_id TEXT,
  issue_type_code TEXT NOT NULL,
  follow_up_status_code TEXT NOT NULL,
  assigned_admin_user_id TEXT,
  priority_code TEXT NOT NULL DEFAULT 'normal',
  created_from_code TEXT NOT NULL,
  route_hint TEXT NOT NULL,
  reason TEXT NOT NULL,
  current_step_code TEXT,
  chat_id INTEGER NOT NULL,
  provider_user_id TEXT,
  locale_code TEXT NOT NULL DEFAULT 'ko',
  recent_messages_summary TEXT,
  failure_count INTEGER NOT NULL DEFAULT 0,
  due_at TEXT,
  assigned_at TEXT,
  first_action_at TEXT,
  closed_at TEXT,
  closure_reason_code TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id),
  FOREIGN KEY (onboarding_session_id) REFERENCES onboarding_sessions(id),
  FOREIGN KEY (assigned_admin_user_id) REFERENCES admin_users(id)
);

CREATE TABLE IF NOT EXISTS admin_follow_up_messages (
  id TEXT PRIMARY KEY,
  admin_follow_up_queue_id TEXT NOT NULL,
  direction_code TEXT NOT NULL,
  message_text TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_id TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (admin_follow_up_queue_id) REFERENCES admin_follow_up_queue(id)
);

CREATE TABLE IF NOT EXISTS admin_follow_up_outcomes (
  id TEXT PRIMARY KEY,
  admin_follow_up_queue_id TEXT NOT NULL,
  outcome_code TEXT NOT NULL,
  note TEXT,
  acted_by_admin_user_id TEXT,
  acted_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (admin_follow_up_queue_id) REFERENCES admin_follow_up_queue(id),
  FOREIGN KEY (acted_by_admin_user_id) REFERENCES admin_users(id)
);

CREATE TABLE IF NOT EXISTS outbox_messages (
  id TEXT PRIMARY KEY,
  admin_follow_up_queue_id TEXT,
  chat_id INTEGER NOT NULL,
  message_text TEXT NOT NULL,
  delivery_state_code TEXT NOT NULL,
  source_code TEXT NOT NULL,
  retry_count INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  sent_at TEXT,
  failed_at TEXT,
  FOREIGN KEY (admin_follow_up_queue_id) REFERENCES admin_follow_up_queue(id)
);

CREATE INDEX IF NOT EXISTS idx_project_invitations_code_status
ON project_invitations(invite_code, invite_status_code);

CREATE INDEX IF NOT EXISTS idx_onboarding_identity_status
ON onboarding_sessions(identity_provider_code, provider_user_id, session_status_code);

CREATE INDEX IF NOT EXISTS idx_admin_follow_up_status_created
ON admin_follow_up_queue(follow_up_status_code, created_at);

CREATE INDEX IF NOT EXISTS idx_outbox_state_created
ON outbox_messages(delivery_state_code, created_at);

CREATE INDEX IF NOT EXISTS idx_channel_messages_chat_time
ON channel_messages(chat_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_follow_up_messages_queue_time
ON admin_follow_up_messages(admin_follow_up_queue_id, created_at);

CREATE INDEX IF NOT EXISTS idx_project_enrollments_participant_status
ON project_enrollments(participant_id, enrollment_status_code);

CREATE INDEX IF NOT EXISTS idx_participant_identities_provider_user
ON participant_identities(identity_provider_code, provider_user_id);

INSERT OR IGNORE INTO admin_users (id, username, display_name, created_at)
VALUES ('admin_local_default', 'local-admin', 'Local Admin', '1970-01-01T00:00:00+00:00');

INSERT OR IGNORE INTO projects (id, project_name, project_status_code, created_at, updated_at)
VALUES ('project_local_default', 'Local Runtime Project', 'active', '1970-01-01T00:00:00+00:00', '1970-01-01T00:00:00+00:00');
