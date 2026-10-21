# Secret input incident response — 2026-10-21

Observed prior screenshot: key-format validation terminated through argparse and
returned to Bash. A later paste could then be executed/echoed as a shell command.
The second reported stop has not been inspected on the server; do not claim a more
specific API cause. Old generic exception handling hid HTTP status diagnostics.

Replaced getpass fallback with Linux /dev/tty + enforced no-echo input. Invalid input
stays inside the reader. Queued multiline paste is flushed before echo is restored.
Core dumps disabled. No key persistence/environment/argv. HTTP failures expose only
status, never response bodies. End/error reader discards input until EXIT. Run using
`exec python3 ... --exec-session` in a dedicated SSH session: exiting closes that
session instead of returning to Bash. Ctrl-C also closes the exec session. No software
can erase screenshots, clipboard history, an existing terminal transcript or a
compromised endpoint; revoke exposed keys as the owner has committed to do.

Verified with a real PTY, fake values only: invalid input not echoed, second pasted
line not echoed, retry remains inside reader, EXIT terminates. History tests verify
secret-bearing line removal, timestamp handling, preservation of ordinary commands,
no duplicate backup, and refusal of symlink history files. No new key or Stripe API
request used to validate this change.

Server remediation must be run by the operator; this environment has no SSH access.
Close other SSH sessions first so their in-memory histories cannot restore secrets.
In the affected Bash, run history -a, then scripts/redact_bash_keys.py with the actual
HISTFILE, then history -c and history -r. The cleaner outputs only count, removes lines
containing Stripe secret/restricted/webhook key patterns, uses an owned regular file,
atomic replacement with mode 0600 and refuses concurrent changes. No secret-bearing
backup is created. Counts establish only what was found in that file, not all logs.
Clear local terminal scrollback by closing its window after the session, clear Windows
clipboard history, and privately address any explicit session transcript/recording.
No root/system audit logs are deleted. Revocation is required regardless of cleanup.

Before a new key: execute onboarding helper with --exec-session --input-self-test and
the existing account ID, type DEMO_ONLY, require SELF_TEST_OK, then type EXIT. Reconnect
with a new dedicated SSH session for the API step only after this succeeds. Run the
updated helper with exec and --exec-session (no self-test), using the same existing
account. Actual API status and requirements remain unverified until that step.
