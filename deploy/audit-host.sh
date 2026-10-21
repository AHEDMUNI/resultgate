#!/bin/sh
# Read-only host inventory. Run interactively; never paste credentials into reports.
set -eu
uname -sr
free -m
df -h / /var
sudo /usr/sbin/sshd -t
sudo /usr/sbin/sshd -T | awk '/^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|allowtcpforwarding|x11forwarding) /'
sudo ufw status verbose
sudo ss -lntup
systemctl is-enabled ssh.service || true
systemctl is-active resultgate.service || true
