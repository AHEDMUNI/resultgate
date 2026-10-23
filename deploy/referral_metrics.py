"""Bounded nginx metrics configuration. No identities, raw URLs or user agents."""
PREFIX = '''# RESULTGATE METRICS START
map $http_user_agent $rg_origin {
    default unknown;
    ~*^ResultGate-Internal internal_declared;
    ~*(bot|crawler|spider|preview|headless) bot_declared;
}
map "$request_method:$status" $rg_count {
    default 0;
    "GET:200" 1;
    "GET:302" 1;
    "GET:304" 1;
}
log_format resultgate_referral escape=json '{"at":"$time_iso8601","event":"$rg_event","origin":"$rg_origin","status":$status}';
# RESULTGATE METRICS END
'''
REDIRECT = '''# RESULTGATE HANDOFF START
    location = /go/browseract {
        if ($request_method != GET) { return 405; }
        if ($args != "") { return 400; }
        set $rg_event browseract_handoff;
        access_log /var/log/nginx/resultgate-access.log resultgate_minimal;
        access_log /var/log/nginx/resultgate-referral.log resultgate_referral if=$rg_count;
        add_header Cache-Control "no-store" always;
        add_header Referrer-Policy "no-referrer" always;
        add_header Strict-Transport-Security "max-age=31536000" always;
        return 302 https://browseract.com?fpr=ahed-ddc97e;
    }
    # RESULTGATE HANDOFF END
'''
LOG = '        access_log /var/log/nginx/resultgate-access.log resultgate_minimal;\n        access_log /var/log/nginx/resultgate-referral.log resultgate_referral if=$rg_count;\n'


def strip(content):
    """Only remove this exact generated instrumentation; unknown edits fail closed."""
    if '# RESULTGATE METRICS START' in content:
        if content.count(PREFIX) != 1 or content.count(REDIRECT) != 1:
            raise ValueError('Unknown metrics configuration; review manually')
        content = content.replace(PREFIX, '', 1).replace(REDIRECT, '', 1)
        for route, event in (('/referrals', 'catalog_html'), ('/referrals.json', 'catalog_json')):
            anchor = f'location = {route} {{\n'
            instrumented = anchor + f'        set $rg_event {event};\n' + LOG
            if content.count(instrumented) != 1:
                raise ValueError('Unknown catalog measurement configuration')
            content = content.replace(instrumented, anchor, 1)
    elif '# RESULTGATE HANDOFF START' in content:
        raise ValueError('Partial metrics configuration')
    return content


def instrument(content):
    if strip(content) != content:
        raise ValueError('Strip existing metrics before rendering')
    for route, event in (('/referrals', 'catalog_html'), ('/referrals.json', 'catalog_json')):
        anchor = f'location = {route} {{\n'
        if content.count(anchor) != 1:
            raise ValueError('Expected one catalog route')
        content = content.replace(anchor, anchor + f'        set $rg_event {event};\n' + LOG)
    if content.count('# RESULTGATE BUSINESS START') != 1:
        raise ValueError('Expected managed static block')
    content = content.replace('# RESULTGATE BUSINESS START', REDIRECT + '# RESULTGATE BUSINESS START', 1)
    return PREFIX + content
