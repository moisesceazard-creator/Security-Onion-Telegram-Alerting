# Testing / Validation Guide

How to safely trigger each rule to confirm the full pipeline works —
Elasticsearch match → `PHTimeEnhancement` → Telegram message → alert
indexed and visible in the SOC UI. Do this on a lab/test segment or with a
throwaway test endpoint where possible, not against production users.

For every rule below, a successful test means: a Telegram message arrives
within roughly one `buffer_time`/`timeframe` window (1–5 minutes, see
[`RULE_REFERENCE.md`](RULE_REFERENCE.md)), **and** the alert appears in the
Security Onion SOC UI under **Alerts** or **Detections** shortly after
(confirms the `indexer` alerter also worked).

You can also dry-run any rule against existing data without waiting for a
live trigger:

```bash
sudo docker exec -it so-elastalert elastalert-test-rule /opt/so/rules/elastalert/<file>.yaml
```

---

### `ssh-bruteforce.yml`

Depends on Security Onion's own built-in `"Security Onion - Grid Node Login
Failure (SSH)"` detection firing first (this rule re-alerts on top of it).

**Trigger:** From a test machine, attempt SSH login to a monitored grid node
with an intentionally wrong password/key a few times:

```bash
ssh baduser@<monitored-node-ip>
```

Confirm the native SSH-failure detection appears in SOC **Alerts** first,
then confirm this rule's Telegram message follows.

### `phishing-malicious-ip.yml`

Depends on a Suricata `ET COMPROMISED Known Feodo C2 IP` signature firing.
**Do this only on an isolated/lab network segment**, since it involves
generating a connection attempt toward a real threat-intel-listed IP (most
listed C2 infrastructure is sinkholed or offline, so this is a network
*flow*, not a working malware connection):

1. Check the current [Feodo Tracker IP blocklist](https://feodotracker.abuse.ch/blocklist/)
   for an IP with an `ET COMPROMISED` signature mapping.
2. From an isolated test host monitored by this Security Onion sensor:
   `curl -m 5 http://<listed-ip>/` (expect it to time out or refuse — that's
   fine, Suricata alerts on the connection attempt itself).

If you'd rather not touch real threat-intel IPs at all, temporarily edit the
rule's `filter.query_string.query` to match a Suricata test signature you
control instead, test, then revert.

### `unauthorized-access.yml`

**Trigger:** On a monitored, Elastic-Agent-enrolled Windows endpoint, fail
to log on or unlock the workstation **3 times within 5 minutes** (wrong
password). This generates Windows Event ID 4625 with logon type 2
(interactive) or 7 (unlock).

### `port-scanning.yml`

**Trigger:** From a source IP that is *not* in the rule's exclusion list, run
a scan touching more than 20 distinct destination ports on a monitored
subnet within 5 minutes:

```bash
nmap -p 1-100 -T4 <target-in-monitored-subnet>
```

### `removable-media.yml`

This rule detects a **marker string**, not raw USB hardware events — it
watches PowerShell process command-line logging for the literal text
`UNAUTHORIZED_USB_STORAGE_CONFIRMED`. This was the tested simulation method
for this capstone; if you have a real endpoint-DLP/USB-blocking product
emitting Windows events, you should replace this rule's `filter` with a
query against that product's actual event ID/log instead.

**Trigger (as originally tested):** On a monitored endpoint with PowerShell
script-block/module logging enabled, run:

```powershell
powershell.exe -Command "# UNAUTHORIZED_USB_STORAGE_CONFIRMED"
```

### `agent-uninstalled.yml`

**Trigger:** On one of the monitored test hostnames listed in the rule's
filter, uninstall or unenroll the Elastic Agent:

```bash
sudo elastic-agent uninstall
```

Confirm the corresponding `.fleet-agents` record flips to `active:false`
with a populated `unenrolled_at`, and that the Telegram alert follows.
**Re-enroll the agent afterward** so the endpoint isn't left unmonitored.

### `new-device.yml` *(disabled by default — enable before testing)*

**Trigger:** Connect a device with an IP inside the monitored subnet
(`192.168.92.0/23` as committed) that hasn't produced Zeek `conn` traffic in
the last 7 days. A previously-unused static IP, or a device that hasn't
connected in over a week, both work.

---

## Recording results for a capstone / report

For each rule, capture: timestamp of trigger, timestamp of Telegram receipt,
and a screenshot of the alert as it appears in the SOC UI. This is the same
evidence pattern used in a detection-accuracy validation table (trigger →
alert generated → alert visible in at least one monitoring component).
