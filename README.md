# Security Onion Real-Time Alerting (Telegram Integration)

Real-time Telegram notifications for high-value [Security Onion](https://securityonion.net/)
detections, built on Security Onion's built-in ElastAlert2 container — no
additional infrastructure required.

Every alert is delivered two ways at once:
- **Telegram** — pushed instantly to an analyst group chat, formatted with
  the relevant MITRE ATT&CK technique and a recommended action.
- **Indexer** — written back into Elasticsearch (`logs-detections.alerts-so-*`),
  so it also appears in the normal Security Onion SOC UI Alerts/Detections
  views.

See [`docs/architecture.md`](docs/architecture.md) for the full data flow
and design rationale.

## Contents

```
Security-Onion-Real-Time-Alerting/
├── detection-rules/          # ElastAlert2 rules deployed on the SO manager
│   ├── ssh-bruteforce.yml
│   ├── phishing-malicious-ip.yml
│   ├── unauthorized-access.yml
│   ├── port-scanning.yml
│   ├── removable-media.yml
│   ├── new-device.yml
│   └── agent-uninstalled.yml
├── enhancements/
│   └── ph-time-enhancement.py   # adds Philippine-time (UTC+8) timestamp to matches
└── docs/
    ├── architecture.md          # system design + data flow diagram
    ├── TELEGRAM_SETUP.md        # bot/chat setup, where secrets live
    └── RULE_REFERENCE.md        # per-rule severity / ATT&CK / trigger table
```

## Quick summary of detections

| Rule | Severity |
|---|---|
| SSH Brute Force | 🔴 Critical |
| Phishing / known-malicious-IP C2 | 🎣 High |
| Unauthorized workstation access | 🟠 High |
| Network reconnaissance / port scan | 🟡 Medium |
| Unauthorized USB / removable media | 🟠 High |
| Elastic Agent uninstalled | 🔴 High |
| New device on LAN *(disabled by default)* | 🟡 Medium |

Full detail in [`docs/RULE_REFERENCE.md`](docs/RULE_REFERENCE.md).

## Setup

This repo contains the rule definitions and enhancement script only — it
assumes an existing Security Onion 2.4 deployment. To deploy:

1. Copy `detection-rules/*.yml` to `/opt/so/rules/elastalert/` on the
   manager (rename as needed to match the `ruleN_*.yaml` convention Security
   Onion expects, or keep as-is — filename is not significant to
   ElastAlert2).
2. Copy `enhancements/ph-time-enhancement.py` to
   `/opt/so/rules/elastalert/ph_time.py` (referenced by rules as
   `rules.ph_time.PHTimeEnhancement`).
3. Configure the Telegram bot and Elasticsearch indexer connection — see
   [`docs/TELEGRAM_SETUP.md`](docs/TELEGRAM_SETUP.md). **This step is not
   optional and involves secrets that must never be committed to this repo.**
4. Re-apply the ElastAlert Salt state / restart the `so-elastalert`
   container.

## Security note

No credentials (Telegram bot token, Elasticsearch password) are stored in
this repository. If you pull rule files directly from a live server, check
for an `indexer_connection:` block before committing — see
[`docs/TELEGRAM_SETUP.md`](docs/TELEGRAM_SETUP.md#3-how-rules-use-it) for
why that can happen and how to strip it.
