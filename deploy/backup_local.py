"""Root-owned local backup job. Seven snapshots maximum; no automatic deletion."""
from pathlib import Path
from datetime import datetime, timezone
import shutil
from resultgate.network.recovery import snapshot


def main():
    root = Path('/var/backups/resultgate')
    if root.is_symlink() or not root.is_dir():
        raise SystemExit('Private backup directory required')
    # Fail visibly rather than grow without bound or delete recovery evidence.
    if len(list(root.iterdir())) >= 7:
        raise SystemExit('Backup retention review required: seven entries reached')
    db = Path('/var/lib/resultgate/delegation.sqlite3')
    if db.is_symlink() or not db.is_file():
        raise SystemExit('Existing database required')
    size = db.stat().st_size
    if size > 256 * 1024 * 1024 or shutil.disk_usage(root).free < 2 * size + 512 * 1024 * 1024:
        raise SystemExit('Backup storage budget exceeded')
    name = datetime.now(timezone.utc).strftime('snapshot-%Y%m%dT%H%M%S%fZ')
    snapshot('/var/lib/resultgate', root / name)
    print('Private local application snapshot completed; no dispatch')

if __name__ == '__main__':
    main()
