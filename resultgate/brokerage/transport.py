"""Fixed public API hosts only; TLS-verified, DNS pinned, no redirects/proxies/credentials."""
import http.client
import ipaddress
import json
import socket
import ssl
import time
from urllib.parse import urlsplit

HOSTS=frozenset({'api.crossref.org','api.datacite.org'})
MAX_RESPONSE=262144

class ProviderFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code=code

def public_addresses(host):
    if host not in HOSTS:
        raise ProviderFailure('host_not_allowed')
    addresses=list(dict.fromkeys(item[4][0] for item in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)))
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ProviderFailure('non_public_address')
    return addresses

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host,timeout=8,context=ssl.create_default_context())
        self.address=address
    def connect(self):
        raw=socket.create_connection((self.address,443),timeout=self.timeout)
        try:
            self.sock=self._context.wrap_socket(raw,server_hostname=self.host)
        except BaseException:
            raw.close()
            raise

def fetch_json(url):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname not in HOSTS or parsed.port not in (None,443) or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ProviderFailure('url_not_allowed')
    conn=None
    try:
        address=public_addresses(parsed.hostname)[0]
        conn=PinnedHTTPS(parsed.hostname,address)
        conn.request('GET',parsed.path,headers={'User-Agent':'ResultGate-brokerage-pilot/0.1 (https://github.com/AHEDMUNI/resultgate)',
            'Accept':'application/json','Accept-Encoding':'identity'})
        response=conn.getresponse()
        if response.status!=200:
            raise ProviderFailure('http_'+str(response.status))
        if response.headers.get('Content-Encoding','identity').lower()!='identity':
            raise ProviderFailure('unsupported_encoding')
        if 'json' not in response.headers.get('Content-Type','').lower():
            raise ProviderFailure('unexpected_content_type')
        body=bytearray()
        deadline=time.monotonic()+10
        while True:
            if time.monotonic()>deadline:
                raise ProviderFailure('timeout')
            chunk=response.read(8192)
            if not chunk: break
            body.extend(chunk)
            if len(body)>MAX_RESPONSE: raise ProviderFailure('response_too_large')
        data=json.loads(body)
        if not isinstance(data,dict): raise ProviderFailure('invalid_response')
        return data
    except ProviderFailure:
        raise
    except (TimeoutError,socket.timeout):
        raise ProviderFailure('timeout') from None
    except (OSError,http.client.HTTPException,ValueError,RecursionError):
        raise ProviderFailure('connection_or_parse_error') from None
    finally:
        if conn is not None: conn.close()
