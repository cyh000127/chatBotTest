# SQLite Backup And Recovery Runbook

## 1. Purpose

This document defines the local operator procedure for backing up and restoring the SQLite runtime database.

The goal is to protect runtime state that must survive restart:

- invitation codes
- onboarding sessions
- admin follow-up queue items
- follow-up messages and outcomes
- outbox delivery state
- admin audit events

This runbook is for local and pilot-grade runtime operations. It does not redefine the production source of truth.

## 2. Backup Principles

Use one of the following two methods:

- cold backup: stop the runtime and copy the database files
- online backup: keep the runtime running and create a logical SQLite backup

Rules:

- keep backup files outside version control
- do not overwrite the active database while the runtime is still writing to it
- keep the database file, WAL file, and SHM file together when using file-copy backup
- treat backup artifacts as sensitive operational data

## 3. Required Inputs

The operator should know these values before starting:

- `SQLITE_DATABASE_PATH`
- backup destination directory
- whether the runtime is stopped or must remain online
- whether `ADMIN_API_ACCESS_TOKEN` is required for verification

Example database path shape:

```env
SQLITE_DATABASE_PATH=C:\runtime-data\messenger-runtime\runtime.sqlite3
```

## 4. Cold Backup Procedure

Use this when a short runtime stop is acceptable.

1. Stop the bot runtime and local Admin API process.
2. Confirm that no process is writing to the database.
3. Copy the database file and sidecar files to a timestamped backup directory.
4. Keep the copied files read-only until backup verification is complete.

PowerShell example:

```powershell
$databasePath = $env:SQLITE_DATABASE_PATH
$backupRoot = "C:\runtime-backups\messenger-runtime"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $backupRoot $timestamp

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item $databasePath $backupDir

if (Test-Path "$databasePath-wal") {
  Copy-Item "$databasePath-wal" $backupDir
}

if (Test-Path "$databasePath-shm") {
  Copy-Item "$databasePath-shm" $backupDir
}
```

## 5. Online Backup Procedure

Use this when the runtime should stay online and you want a consistent logical snapshot.

Python includes SQLite support by default, so an external SQLite CLI is not required.

PowerShell example:

```powershell
$databasePath = $env:SQLITE_DATABASE_PATH
$backupRoot = "C:\runtime-backups\messenger-runtime"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $backupRoot "runtime-$timestamp.sqlite3"

New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

@'
import sqlite3
import sys

source_path = sys.argv[1]
backup_path = sys.argv[2]

source = sqlite3.connect(source_path)
target = sqlite3.connect(backup_path)
try:
    source.backup(target)
finally:
    target.close()
    source.close()
'@ | python - $databasePath $backupPath
```

## 6. Backup Verification

After backup creation, verify the artifact before treating it as usable.

Minimum checks:

1. confirm the backup file exists
2. confirm the backup file size is greater than zero
3. open the backup database in read-only mode
4. confirm key tables exist

PowerShell verification example:

```powershell
$backupPath = "C:\runtime-backups\messenger-runtime\runtime-20260427-120000.sqlite3"

@'
import sqlite3
import sys

connection = sqlite3.connect(sys.argv[1])
try:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    print([row[0] for row in rows if row[0] in {
        "project_invitations",
        "onboarding_sessions",
        "admin_follow_up_queue",
        "outbox_messages",
        "admin_audit_events",
    }])
finally:
    connection.close()
'@ | python - $backupPath
```

## 7. Restore Procedure

Use restore only when you intentionally want to roll the local runtime state back to a known backup.

1. Stop the bot runtime and local Admin API process.
2. Choose the backup set to restore.
3. Move the current database files to a quarantine directory instead of deleting them immediately.
4. Copy the selected backup database into the active `SQLITE_DATABASE_PATH`.
5. If the backup was created by cold file copy and includes `-wal` or `-shm`, restore those sidecar files together.
6. Start the runtime again.
7. Run the post-restore verification steps.

PowerShell example:

```powershell
$databasePath = $env:SQLITE_DATABASE_PATH
$restoreSource = "C:\runtime-backups\messenger-runtime\runtime-20260427-120000.sqlite3"
$quarantineRoot = "C:\runtime-backups\messenger-runtime\quarantine"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$quarantineDir = Join-Path $quarantineRoot $timestamp

New-Item -ItemType Directory -Path $quarantineDir -Force | Out-Null

if (Test-Path $databasePath) {
  Move-Item $databasePath $quarantineDir
}

if (Test-Path "$databasePath-wal") {
  Move-Item "$databasePath-wal" $quarantineDir
}

if (Test-Path "$databasePath-shm") {
  Move-Item "$databasePath-shm" $quarantineDir
}

Copy-Item $restoreSource $databasePath
```

## 8. Post-Restore Verification

After restart, verify both the process and the restored state.

Minimum checks:

1. `GET /healthz` returns `200`
2. `GET /admin/runtime-summary` returns expected queue and outbox counts
3. `GET /admin/follow-ups` returns expected open or closed items
4. `GET /admin/outbox` returns expected delivery backlog
5. if enabled, `GET /admin/audit-events` is readable

PowerShell examples:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/healthz"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/admin/runtime-summary"
```

If admin token protection is enabled:

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/admin/runtime-summary" `
  -Headers @{ "X-Admin-Token" = $env:ADMIN_API_ACCESS_TOKEN }
```

## 9. Failure Handling Rules

If restore verification fails:

- stop the runtime again
- do not continue writing new runtime state
- compare the restored database with the quarantined database
- retry with a different backup only after documenting the failed attempt

If both the restored copy and the active copy look damaged, treat the runtime as needing manual local recovery. Do not fabricate queue state, onboarding approval state, or audit history.

## 10. Operator Notes

- do not commit database files, WAL files, SHM files, or backup archives
- do not paste access tokens into backup filenames or notes
- do not use reset-by-delete as the default recovery method when the runtime data matters
- document the backup timestamp and restore timestamp whenever you perform a rollback
