# Secret input incident response — 2026-10-21

Observed prior screenshot: key-format validation terminated through argparse and
returned to Bash. A later paste could then be executed/echoed as a shell command.
A later screenshot established a second bug: ASCII decoding rejected non-ASCII
terminal input, and the error handler repeated the same failing reader. UTF-8
replacement decoding now safely rejects invalid key input without crashing.
Old generic exception handling hid HTTP status diagnostics.

Replaced getpass fallback with Linux /dev/tty + enforced no-echo input. Invalid input
stays inside the reader. Queued multiline paste is flushed before echo is restored.
Core dumps disabled. No key persistence/environment/argv. HTTP failures expose only
status, never response bodies. End/error reader discards input until an empty Enter or EXIT. Run using
`exec python3 ... --exec-session` in a dedicated SSH session: exiting closes that
session instead of returning to Bash. Ctrl-C also closes the exec session. No software
can erase screenshots, clipboard history, an existing terminal transcript or a
compromised endpoint; revoke exposed keys as the owner has committed to do.

Verified with a real PTY, fake values only (including Arabic input): invalid input not echoed, second pasted
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
the existing account ID, type 123456, require SELF_TEST_OK, then press Enter. Reconnect
with a new dedicated SSH session for the API step only after this succeeds. Run the
updated helper with exec and --exec-session (no self-test), using the same existing
account. Actual API status and requirements remain unverified until that step.

Operator screenshot confirmed removal of five matching Bash-history lines. This
does not establish cleanup of other logs or revocation. Four focused tests pass,
including Unicode/malformed input at the finish prompt. Self-test retries safely
and makes no Stripe request.
