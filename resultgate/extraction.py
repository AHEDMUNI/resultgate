"""Deterministic checks against caller-supplied evidence, not a truth oracle."""
import json
import re

MAX_BYTES = 1048576
MISSING = object()


def bounded(payload):
    stack = [(payload, 0)]
    nodes = 0
    while stack:
        nodes += 1
        if nodes > 100000:
            raise ValueError("maximum JSON node count is 100000")
        value, depth = stack.pop()
        if depth > 32:
            raise ValueError('maximum nesting depth is 32')
        if isinstance(value, dict):
            if not all(isinstance(k, str) for k in value):
                raise ValueError('keys must be strings')
            stack.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            stack.extend((v, depth + 1) for v in value)
    try:
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError('input must be finite JSON') from exc
    if len(encoded) > MAX_BYTES:
        raise ValueError('input exceeds 1 MiB')


def pointer(value):
    if not isinstance(value, str) or not value.startswith('/') or len(value) > 512:
        raise ValueError('field must be a non-root JSON pointer, up to 512 characters')
    if re.search(r'~(?![01])', value):
        raise ValueError('invalid JSON pointer escape')
    return [p.replace('~1', '/').replace('~0', '~') for p in value[1:].split('/')]


def lookup(record, path):
    for part in path:
        if isinstance(record, dict):
            record = record.get(part, MISSING)
        elif isinstance(record, list) and re.fullmatch(r'0|[1-9][0-9]*', part):
            idx = int(part)
            record = record[idx] if idx < len(record) else MISSING
        else:
            return MISSING
    return record


def absent(v):
    return v is MISSING or v is None or (isinstance(v, str) and not v.strip())


def audit_extraction(payload: dict) -> dict:
    bounded(payload)
    allowed = {'records', 'required_fields', 'unique_fields', 'expected_count', 'job_status',
               'next_cursor', 'seen_cursors', 'truncated'}
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise ValueError('expected extraction object with documented keys')
    records = payload.get('records')
    if not isinstance(records, list) or len(records) > 5000 or not all(isinstance(r, dict) for r in records):
        raise ValueError('records must be at most 5000 objects')
    paths = {}
    for key in ('required_fields', 'unique_fields'):
        fields = payload.get(key, [])
        if not isinstance(fields, list) or len(fields) > 64:
            raise ValueError('fields must be arrays of at most 64 pointers')
        paths[key] = [(p, pointer(p)) for p in fields]
    count = payload.get('expected_count')
    if 'expected_count' in payload and (type(count) is not int or count < 0):
        raise ValueError('expected_count must be a nonnegative integer')
    state = payload.get('job_status', 'unknown')
    if state not in ('completed', 'failed', 'cancelled', 'scraping', 'unknown'):
        raise ValueError('invalid job_status')
    next_cursor = payload.get('next_cursor')
    if next_cursor is not None and (not isinstance(next_cursor, str) or not next_cursor or len(next_cursor) > 2048):
        raise ValueError('next_cursor must be null or nonempty string up to 2048 characters')
    seen = payload.get('seen_cursors', [])
    if not isinstance(seen, list) or len(seen) > 5000 or not all(isinstance(c, str) and 0 < len(c) <= 2048 for c in seen):
        raise ValueError('seen_cursors must be bounded nonempty strings')
    if 'truncated' in payload and type(payload['truncated']) is not bool:
        raise ValueError('truncated must be boolean')
    findings = []
    total_findings = 0
    def add(code, **details):
        nonlocal total_findings
        total_findings += 1
        if len(findings) < 100:
            findings.append({'code': code, **details})
    if state in ('failed', 'cancelled'):
        add('UPSTREAM_FAILED')
    elif state == 'scraping':
        add('UPSTREAM_INCOMPLETE')
    if next_cursor is not None:
        add('PAGINATION_PENDING')
    if len(set(seen)) != len(seen) or next_cursor is not None and next_cursor in seen:
        add('CURSOR_CYCLE')
    if payload.get('truncated'):
        add('TRUNCATED')
    if count is not None and len(records) != count:
        add('COUNT_MISMATCH', expected=count, actual=len(records))
    keys = set()
    for index, record in enumerate(records):
        for field, path in paths['required_fields']:
            if absent(lookup(record, path)):
                add('REQUIRED_FIELD_MISSING', record_index=index, field=field)
        if paths['unique_fields']:
            values = [lookup(record, p) for _, p in paths['unique_fields']]
            if any(absent(v) for v in values):
                add('UNIQUE_KEY_MISSING', record_index=index)
            else:
                key = json.dumps(values, sort_keys=True, ensure_ascii=False, allow_nan=False)
                if key in keys:
                    add('DUPLICATE_KEY', record_index=index)
                keys.add(key)
    unknown = []
    if count is None:
        unknown.append('expected_count')
    if state == 'unknown':
        unknown.append('job_status')
    for key in ('next_cursor', 'truncated'):
        if key not in payload:
            unknown.append(key)
    return {'status': 'fail' if total_findings else 'unknown' if unknown else 'pass',
            'scope': 'caller_supplied_contract_only', 'source_authenticity': 'not_verified',
            'semantic_accuracy': 'not_evaluated', 'records_checked': len(records),
            'findings': findings, 'finding_count': total_findings,
            'findings_truncated': total_findings > len(findings), 'missing_evidence': unknown}
