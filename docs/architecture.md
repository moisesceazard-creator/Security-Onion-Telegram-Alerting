# Architecture — Security Onion Real-Time Alerting (ElastAlert2 → Telegram)

## 1. Overview

This project adds a real-time notification layer on top of a standard
[Security Onion](https://securityonion.net/) 2.4 deployment. Security Onion already
collects and indexes network and endpoint telemetry (Zeek, Suricata, Elastic Agent /
Winlogbeat) into Elasticsearch and surfaces it through the SOC web UI. What it does
**not** do out of the box is push a subset of high-value detections to an
analyst's phone the moment they happen.

This repo adds that layer using Security Onion's built-in **ElastAlert2**
container, a small set of **custom detection rules**, one **custom match
enhancement** (Philippine-time timestamp conversion), and Telegram as the
notification channel — while also writing every fired alert back into
Elasticsearch so it still shows up in the normal SOC Alerts/Detections views.

## 2. Data flow

```
 ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐
 │  Zeek/Suricata│  │ Elastic Agent│  │ Windows Event Logs  │
 │  (network)    │  │ (endpoint)   │  │ (via Elastic Agent) │
 └──────┬───────┘  └──────┬───────┘  └──────────┬──────────┘
        │                 │                     │
        └────────────┬────┴──────────┬──────────┘
                      ▼               ▼
              ┌──────────────────────────────┐
              │        Elasticsearch          │
              │  logs-zeek-so-*                │
              │  logs-suricata.alerts-so-*      │
              │  logs-system.security-default-* │
              │  logs-windows.powershell-default-*│
              │  .fleet-agents                 │
              └───────────────┬───────────────┘
                              │  scheduled queries (every N min)
                              ▼
                    ┌───────────────────┐
                    │  so-elastalert     │
                    │  (ElastAlert2)     │
                    │  detection-rules/* │
                    └─────────┬─────────┘
                              │ match found
                              ▼
                 ┌─────────────────────────┐
                 │ enhancements/           │
                 │ ph-time-enhancement.py  │
                 │ (adds time_ph field,    │
                 │  UTC+8 / Philippine     │
                 │  Standard Time)         │
                 └────────────┬────────────┘
                              │
              ┌───────────────┴────────────────┐
              ▼                                 ▼
   ┌─────────────────────┐          ┌────────────────────────┐
   │  Telegram alerter    │          │  indexer alerter        │
   │  → Bot API →          │          │  → writes back into     │
   │    analyst group chat │          │    logs-detections      │
   │    (real-time push)   │          │    .alerts-so-* index   │
   └─────────────────────┘          │  → visible in SOC UI    │
                                     │    Alerts / Detections   │
                                     └────────────────────────┘
```

## 3. Components

### 3.1 Detection rules (`detection-rules/`)

Each file is a standard ElastAlert2 rule deployed to the Security Onion
manager under `/opt/so/rules/elastalert/` (enabled) or
`/opt/so/rules/elastalert_disabled/` (present but not yet active). Every rule:

- Queries a specific Elasticsearch index pattern populated by Security Onion's
  existing pipelines (no new log source required).
- Runs the `PHTimeEnhancement` match enhancement to attach a
  human-readable Philippine-time timestamp (`time_ph`) to the match.
- Fires two alerters on match: `telegram` (real-time push) and `indexer`
  (writes the alert into `logs-detections.alerts-so-*` so it is also
  queryable/visible from the normal Security Onion Alerts and Detections
  screens, not just Telegram).
- Carries a `rule.uuid`, MITRE ATT&CK reference, and severity mapping
  (`event.severity` / `sigma_level`) so it behaves like a native Security
  Onion detection once indexed.

See [`RULE_REFERENCE.md`](RULE_REFERENCE.md) for the full list, thresholds,
and ATT&CK mapping.

### 3.2 Match enhancement (`enhancements/ph-time-enhancement.py`)

ElastAlert2 timestamps are UTC by default. `PHTimeEnhancement` converts the
match's `@timestamp` to `Asia/Manila` local time (UTC+8) and stores it as
`time_ph`, which every rule references in its Telegram message body so
analysts see a time they don't have to mentally convert.

### 3.3 Alerters

- **Telegram** — built into ElastAlert2 (`elastalert.alerts.TelegramAlerter`,
  invoked simply as `telegram` in each rule's `alert:` list). Configured once,
  globally, via `telegram_bot_token` and `telegram_room_id` in the
  ElastAlert2 pillar (see [`TELEGRAM_SETUP.md`](TELEGRAM_SETUP.md)) — not
  per-rule.
- **Indexer** — also built into ElastAlert2 (`elastalert.alerts.ElasticsearchAlerter`,
  invoked as `indexer`). Writes each fired alert as a document into the
  `logs-detections.alerts-so-*` index using the connection settings and
  document shape defined under each rule's `indexer_alert_config`. This is
  what makes ElastAlert-driven detections show up alongside native Security
  Onion detections in the SOC UI instead of only existing as a Telegram
  message.

There is **no custom Python alerter class** in this project — `indexer` is
the stock ElastAlert2 alerter, referenced by name.

### 3.4 Deployment

Rules and the enhancement module live on the Security Onion manager under
`/opt/so/rules/elastalert/` and are picked up by the `so-elastalert` Docker
container (part of the standard Security Onion stack — no additional
services were installed). Enabling/disabling a rule is done by moving it
between `/opt/so/rules/elastalert/` and `/opt/so/rules/elastalert_disabled/`
and re-running the ElastAlert Salt state.

## 4. Why this design

- **No new infrastructure.** Everything rides on ElastAlert2, which already
  ships with Security Onion — this is configuration, not a new service.
- **Dual delivery.** Telegram gives sub-minute human notification; the
  `indexer` alerter keeps every fired alert queryable in Elasticsearch/Kibana
  and visible in the SOC Alerts view, so nothing is Telegram-only and lost if
  a phone notification is missed.
- **Analyst-first message format.** Each Telegram message maps directly to an
  action (block IP, isolate host, verify device) and a MITRE ATT&CK technique,
  so the on-call person doesn't have to pivot to the SOC UI just to decide
  whether to escalate.

## 5. Related documents in this repo

- [`RULE_REFERENCE.md`](RULE_REFERENCE.md) — per-rule detail table.
- [`TELEGRAM_SETUP.md`](TELEGRAM_SETUP.md) — how to configure the bot/chat
  and where secrets live (not in this repo).
