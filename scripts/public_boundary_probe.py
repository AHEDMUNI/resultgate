"""Read-only fixed-host checks. No tokens, paid calls, bodies, task/user metrics."""
import json
import ssl
import sys
import time
import urllib.error
import urllib.request

BASE = 'https://agents.allubiyerbamate.com'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe():
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    checks = [('/mcp', 'GET', None, {}, 401),
              ('/mcp', 'POST', b'{}', {'Content-Type': 'application/json'}, 401),
              ('/healthz', 'GET', None, {}, 404), ('/v1/capabilities', 'GET', None, {}, 404)]
    results = []
    for path, method, data, headers, expected in checks:
        started = time.monotonic()
        try:
            request = urllib.request.Request(BASE+path, data=data, headers=headers, method=method)
            with opener.open(request, timeout=10) as response:
                status = response.status
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
        except (OSError, ValueError):
            status = None
        results.append({'path': path, 'method': method, 'status': status, 'expected': expected,
                        'passed': status == expected, 'milliseconds': round((time.monotonic()-started)*1000)})
    return {'checks': results, 'passed': all(x['passed'] for x in results),
            'scope': 'TLS verification and anonymous boundary only; not authenticated health, tenant isolation or adoption'}


if __name__ == '__main__':
    result = probe()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['passed'] else 1)
