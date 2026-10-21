"""Session-only referral ledger: no raw identifiers, prompts, response bodies or claims of commission."""
import hmac
import secrets
import threading
import time

class Ledger:
    def __init__(self):
        self.lock=threading.RLock()
        self.secret=secrets.token_bytes(32)
        self.events={}
        self.keys={}
    def digest(self,value):
        return hmac.digest(self.secret,value.encode(),'sha256').hex()
    def purge(self):
        expired=[k for k,v in self.events.items() if time.monotonic()-v['_created']>3600]
        for key in expired:
            self.keys.pop(self.events[key]['_key'],None)
            del self.events[key]
    def view(self,route_id):
        with self.lock:
            self.purge()
            if route_id not in self.events: raise ValueError('unknown or expired route')
            e=self.events[route_id]
            return {k:v for k,v in e.items() if not k.startswith('_')}
