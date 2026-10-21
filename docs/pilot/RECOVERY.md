# Local backup and restore readiness

`python -m resultgate.network.recovery` creates a consistent SQLite snapshot and
copies the same 32-byte identity key into a new private directory. The key is
required to preserve pseudonymous tenant/token hashes and idempotency identity.
It is never printed. The snapshot is sensitive: it contains authentication hashes,
provider/task metadata and the identity key. Do not commit, attach to GitHub Issues,
or publish it as a CI artifact.

```sh
python -m resultgate.network.recovery snapshot \
  --source /PRIVATE/current-registry --destination /PRIVATE/new-snapshot
python -m resultgate.network.recovery restore \
  --source /PRIVATE/new-snapshot --destination /PRIVATE/new-offline-registry \
  --acknowledge-offline-reconciliation
```

Use existing private parent directories. Both commands refuse to overwrite or
merge destinations, reject symlink paths/members and create files with mode 0600
inside a mode-0700 directory. SQLite's backup API captures committed WAL data;
copying only the main `.sqlite3` file with a normal file-copy tool is unsafe.
The backup copy has a 30-second progress budget; a busy or oversized snapshot
fails instead of retrying forever. Database integrity is checked. A manifest detects accidental corruption of the
database or identity key; it is not a cryptographic signature against a malicious
administrator who can replace the manifest. The local filesystem owner remains
the trust boundary. Prevent identity rotation while taking a snapshot and prevent
changes to a snapshot while restoring it.

The commands do not initialize Registry, purge records, execute tasks, call a
provider, provision cloud storage or create a scheduled backup. Existing 30-day
application retention still applies when a restored Registry is later opened.
No off-host copy, encryption-at-rest service or disaster-recovery guarantee is
implemented. Production storage must add encrypted off-host copies, access control,
retention, scheduled verification and regular restore drills.

## Critical restore procedure

1. Stop all workers and ingress that could dispatch work; isolate the restore host
   from provider credentials/network access. Never restore over a running database.
2. Restore to a **new offline directory**. The tool writes
   `RESTORE-RECONCILIATION-REQUIRED.json`. `Store` checks this marker before opening
   or purging the database and refuses startup. Registry, market and the local
   gateway therefore fail closed on this restored directory. This is not a lock
   on unrelated journals, direct SQLite access or a privileged operator.
3. Reconcile both in-flight tasks and **all work submitted after the snapshot's
   timestamp** against authoritative provider records. An old snapshot may lack
   a consumed dispatch reservation; replay could spend twice. Keep provider
   credentials disabled if reconciliation cannot establish the outcome.
4. Validate tenant isolation, tokens, provider approvals, quotas and idempotency in
   the isolated copy. Rotate/reissue credentials deliberately where required.
5. Only after documented reconciliation may the trusted local operator remove
   the quarantine marker. There is no HTTP/MCP unquarantine endpoint. Require a
   separate deployment decision before enabling ingress/workers. Restoring and
   removing a marker do not authorize spending.

The Browser Use one-shot trial uses a separate journal and historical runner;
this Registry snapshot is **not** a backup of that journal. Its consumed task must
never be recreated from a new directory. Use the existing execution evidence and
provider reconciliation, not a new paid test.

## Free verification

```sh
python -m unittest discover -s tests -p test_recovery.py -v
```

Tests cover unchanged tenant/token and unique request identity, preserved pending
task state, enforced Registry startup quarantine, WAL commits, private file modes, corruption, missing acknowledgement,
symlink refusal and no overwrite. These tests demonstrate a local recovery drill,
not a publicly hosted network or scheduled off-host recovery service.
