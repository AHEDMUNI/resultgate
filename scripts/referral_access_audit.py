"""Read existing minimal nginx logs; emit aggregates only, never raw lines/IPs."""
import gzip
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def audit(folder=Path('/var/log/nginx')):
    counts = Counter()
    recognized = skipped = 0
    unavailable = []
    paths = sorted(folder.glob('resultgate-access.log*'))
    pattern = re.compile(r'(\S+) ([1-5]\d\d) (\d+(?:\.\d+)?)\s*')
    for path in paths:
        if path.is_symlink() or not path.is_file():
            unavailable.append(path.name)
            continue
        try:
            opener = gzip.open if path.suffix == '.gz' else open
            with opener(path, 'rt', encoding='utf-8', errors='replace') as stream:
                for line in stream:
                    match = pattern.fullmatch(line)
                    try:
                        if not match:
                            raise ValueError()
                        timestamp = datetime.fromisoformat(match[1])
                        if timestamp.tzinfo is None:
                            raise ValueError()
                    except ValueError:
                        skipped += 1
                        continue
                    day = timestamp.astimezone(ZoneInfo('America/Chicago')).date().isoformat()
                    counts[(day, match[2])] += 1
                    recognized += 1
        except (OSError, EOFError):
            unavailable.append(path.name)
    return {
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'source': 'existing_resultgate_minimal_nginx_logs',
        'files_found': len(paths), 'unreadable_files': unavailable,
        'recognized_requests': recognized if paths and not unavailable else None,
        'unparsed_lines': skipped,
        'daily_status_counts': [dict(day=d, status=int(s), requests=n)
                                for (d, s), n in sorted(counts.items())],
        'independent_visitors': None, 'recommendation_requests': None,
        'referral_clicks': None,
        'limitation': 'HTTP requests include internal probes and bots. This format has no path, source or visitor identity. Counts cannot establish independent reach or clicks. Unparsed lines and unavailable files are not zero traffic.',
    }


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
