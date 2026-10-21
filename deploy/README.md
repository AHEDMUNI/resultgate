# Private server preparation — not deployed

2026-10-21 America/Chicago. PRs 4,5,6 were open at inspection. This work is
stacked on PR6; no merge or release is required to review a pinned pilot checkout.
The owner reports an Ubuntu24.04/1GiB host with SSH-only UFW and weekly DO backups.
Those host properties have NOT been independently verified in this environment.
No SSH agent/default identity was available, and TCP connection to port22 failed
from the execution environment. This does not prove SSH is down for the owner.
No credential was generated/copied, no host setting changed and no paid task ran.

## Access first

Use the existing key on its current trusted computer. Never upload its private
half/passphrase to chat, GitHub, a workflow or a support form. Obtain the host's
public key fingerprint through the already-authenticated DigitalOcean console:

```
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Compare that fingerprint when first connecting from the trusted computer:

```
ssh -o StrictHostKeyChecking=ask resultgateadmin@64.227.3.178
```

Do not use StrictHostKeyChecking=no, expose root/password login or open more
ports to fix the assistant's connectivity. If operator assistance via browser
console is needed, the owner should open the existing Droplet Console and enter
credentials themselves. Never create an SSH private key in this repository.

Run `sh deploy/audit-host.sh` from reviewed source after access. Review listeners,
IPv4/IPv6 firewall rules, effective SSH config (including Match clauses), cloud
firewall if any, available RAM/disk and installed services. Keep the existing SSH
session and console open before contemplating access-policy changes. This package
makes NO SSH/UFW edits. An external authorized scan is still needed to corroborate
host listeners/firewall; none was completed here.

## Installation sequence (operator review; not yet run on host)

Use a reviewed immutable commit from this PR in /opt/resultgate/source. Check the
commit SHA before executing anything; do not install a moving branch with sudo.
Read deployment scripts first. No curl-pipe-shell, Docker, database server, worker
pool or Browser Use key is needed. Ubuntu Python3.12 and python3-venv suffice.

1. Install `python3-venv` and `git` with Ubuntu apt after checking free disk.
2. Create dedicated `resultgate` system user/group with nologin shell, no sudo,
   and home /var/lib/resultgate. Do not reuse resultgateadmin for app execution.
3. Root owns /opt/resultgate and source/venv/ops; app must not write its code.
   Create /var/lib/resultgate as resultgate:resultgate0700 and
   /var/backups/resultgate as root:root0700. Reject unexpected existing symlinks.
4. Create /opt/resultgate/venv via python3 -m venv. Install the reviewed source
   with pip --no-cache-dir (runtime dependencies only). Do not install development
   test/build tooling onto the1GiB host. Record installed versions and source SHA.
5. Initialize only if no identity/database exists:

```
sudo -u resultgate /opt/resultgate/venv/bin/python -I -c 'from resultgate.network.registry import Registry; r=Registry("/var/lib/resultgate"); r.db.close()'
```

6. Copy backup_local.py to /opt/resultgate/ops/backup_local.py root-owned0644.
   Copy service/timer files to /etc/systemd/system root-owned0644 and
   journald@resultgate.conf to /etc/systemd/journald@resultgate.conf. Inspect any
   existing unit/config first; do not overwrite an unrelated service.
7. Run systemd-analyze verify on the installed unit files, then daemon-reload.
   Start resultgate.service and confirm local health before enable. Do not open UFW.

```
sudo systemctl start resultgate.service
curl --noproxy '*' --fail --max-time 3 http://127.0.0.1:8765/healthz
sudo systemctl status resultgate.service --no-pager
sudo systemctl show resultgate.service -p User -p MemoryCurrent -p MemoryPeak -p MemoryMax -p NRestarts
sudo ss -lntup
```

8. If checks pass, enable resultgate.service. Test restart, local health and
   persistent task identity using synthetic internal fixtures only. A controlled
   VM reboot requires confirming console/reconnect access with the owner first.
   `is-enabled` is not evidence of a successful real reboot.
9. Start resultgate-backup.service manually, inspect success, run the separate
   quarantined restore drill in docs/pilot/RECOVERY.md, then enable/start the
   backup timer. Never restore over production data.

## Security and limits

App binds127.0.0.1:8765. OS unit additionally permits loopback IP only; verify
kernel cgroup/BPF enforcement on the actual host, since unsupported restrictions
can warn rather than protect. No ingress/public proxy is configured. Health checks
only local DB readability, never provider availability or commercial readiness.
Authenticated API remains simulation-only, with zero authorized execution budget.
No tokens are provisioned by this deployment, and no provider secrets are loaded.

App MemoryHigh256MiB/MemoryMax384MiB, no swap allowance, CPU70%, tasks64 and fd1024.
Backup MemoryMax192MiB/CPU25% runs separately; memory caps are ceilings, not measured
RAM demand. System journal namespace caps persistent use32MiB and runtime8MiB with
7-day retention and rate limits. Verify namespace/journal disk use on the host.
The app can restart five times/5minutes; repeated failure then requires inspection.
No automatic recovery sends tasks or clears restore quarantine.

Backup job uses SQLite snapshot API, includes identity.key privately and stops
with an explicit failure at seven snapshots, DB>256MiB or inadequate free space.
It deliberately does not delete recovery evidence. Operator must archive/prune
reviewed snapshots before day8; otherwise new backups stop. Timer failures need
operator monitoring (`systemctl --failed`, journal); no alert delivery is installed.
Local snapshots are not disaster recovery. DO weekly backups are owner-reported;
verify inclusion and recovery on DO without creating additional paid resources.
No additional off-host storage/subscription has been activated. This is a bounded
pilot procedure, not unattended production backup management.

## Validation actually completed

253 local tests passed, including a real child-process stop/start with a persistent
SQLite task, unchanged ID and duplicate=true on retry. Existing recovery tests
verify private snapshot/restore quarantine. Bandit and diff checks passed.
Systemd255 parser reported only missing /opt/resultgate/venv/bin/python in this
preparation environment; actual unit startup/resource enforcement/reboot on the
Droplet have not been tested. No claim of remote deployment or host security.

1GiB is a candidate for one small Python process+SQLite, not browser/LLM execution.
Measure idle/peak RSS, OOMs, latency and backup overlap on the actual server before
claiming capacity. Run no browser or model on this host. Upgrade is not authorized.

Sources: https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html
https://www.freedesktop.org/software/systemd/man/255/systemd.resource-control.html
https://documentation.ubuntu.com/server/how-to/security/openssh-server/
