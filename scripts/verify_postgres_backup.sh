#!/usr/bin/env bash
# Validate a downloaded PostgreSQL custom-format backup before a restore drill.
# Usage: bash scripts/verify_postgres_backup.sh /path/to/backup.dump
set -euo pipefail

backup="${1:-}"
if [[ -z "$backup" || ! -f "$backup" ]]; then
  echo "Usage: $0 /path/to/backup.dump" >&2
  exit 2
fi
if ! command -v pg_restore >/dev/null 2>&1; then
  echo "pg_restore is required (install PostgreSQL client tools)." >&2
  exit 2
fi
pg_restore --list "$backup" >/tmp/sportshub-backup-contents.txt
if ! grep -Eq 'TABLE DATA|TABLE ' /tmp/sportshub-backup-contents.txt; then
  echo "Backup archive has no table entries; refusing to mark it valid." >&2
  exit 1
fi
echo "Backup archive is readable and contains table entries."
echo "This validates archive structure only; restore into a disposable database to verify recoverability."
