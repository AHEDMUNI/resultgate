#!/usr/bin/env python3
"""Remove Stripe secret-bearing history lines; output counts only, never values.
Run after `history -a`, followed by `history -c; history -r` in that same Bash.
No backup is created because it would retain the exposed key.
"""
import os
from pathlib import Path
import re
import stat
import tempfile

SECRET = re.compile(rb'(?:[sr]k_(?:test|live)_|whsec_)[A-Za-z0-9_]+')


def scrub(path):
    path=Path(path)
    if not path.exists(): return 0
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError('history must be an owned regular file, not a symlink')
    raw=path.read_bytes(); lines=raw.splitlines(keepends=True)
    clean=[]; count=0
    for line in lines:
        if SECRET.search(line):
            count+=1
            if clean and re.fullmatch(rb'#[0-9]+\s*',clean[-1]): clean.pop()
        else: clean.append(line)
    if not count: return 0
    fd,temp=tempfile.mkstemp(prefix='.history-clean-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(b''.join(clean)); stream.flush(); os.fsync(stream.fileno())
        if path.read_bytes()!=raw: raise ValueError('history changed; close other sessions and retry')
        os.replace(temp,path)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return count


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path');a=p.parse_args()
    try: print('Removed secret-bearing history lines:',scrub(a.path))
    except (OSError,ValueError): raise SystemExit('History cleanup stopped; no sensitive content displayed.')
