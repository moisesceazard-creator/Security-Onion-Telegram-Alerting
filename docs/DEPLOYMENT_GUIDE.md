# Deployment Guide — Replicating This Setup

This walks through deploying this project on a fresh Security Onion install,
start to finish. It assumes no prior familiarity with this repo.

## 0. Prerequisites

- A working **Security Onion 2.4.x** deployment (Standalone, Manager, or
  Manager Search grid role) — this project was built and tested on
  **2.4.210, Standalone mode**. The `so-elastalert` container ships with
  every Security Onion installation by default; no extra package install is
  required.
- At least one active log source feeding the indices these rules query:
  Zeek (network), Suricata (IDS alerts), and Elastic Agent enrolled on at
  least one Windows endpoint (for the Windows-log-based rules). If you don't
  run one of these sources, remove or skip the corresponding rule.
- SSH/console access to the manager with `sudo`.
- A Telegram account to create a bot (see
  [`TELEGRAM_SETUP.md`](TELEGRAM_SETUP.md)).

## 1. Confirm ElastAlert2 is running

```bash
sudo so-status | grep -i elastalert
# or
sudo docker ps --filter name=elastalert
```

You should see `so-elastalert` as `Up`. If it isn't running, check
`Administration → Grid` in the SOC UI, or `sudo so-elastalert-restart`.

## 2. Deploy the match enhancement

Copy the enhancement module into the same directory ElastAlert2 loads rules
from:

```bash
sudo cp enhancements/ph-time-enhancement.py /opt/so/rules/elastalert/ph_time.py
sudo chown elastalert:elastalert /opt/so/rules/elastalert/ph_time.py
```

Every rule in this repo references it as `rules.ph_time.PHTimeEnhancement` —
the filename (`ph_time.py`) and module path must match, or the rule will
fail to load. Adjust `timedelta(hours=8)` in the script if your analysts are
not in a UTC+8 timezone.

## 3. Deploy detection rules

```bash
sudo cp detection-rules/*.yml /opt/so/rules/elastalert/
```

You can rename files freely (e.g. back to the `ruleN_description.yaml`
convention used on the original deployment) — ElastAlert2 does not care
about filename, only content.

If you don't want `new-device.yml` active immediately (it re-alerts on every
first-seen IP for 7 days, which can be noisy on a large/unfamiliar network),
put it in the disabled rules directory instead:

```bash
sudo mkdir -p /opt/so/rules/elastalert_disabled
sudo mv /opt/so/rules/elastalert/new-device.yml /opt/so/rules/elastalert_disabled/
```

## 4. Adjust environment-specific values

Before going further, edit these rules to match **your** network — as
committed, they reflect the original deployment's environment:

| Rule | What to change |
|---|---|
| `port-scanning.yml` | Exclusion list of internal IPs that legitimately touch many ports (backup jobs, scanners, monitoring tools) |
| `new-device.yml` | The monitored subnet (`192.168.92.0/23`) |
| `agent-uninstalled.yml` | The list of monitored endpoint hostnames |

## 5. Configure Telegram + Elasticsearch indexer connection

Follow [`TELEGRAM_SETUP.md`](TELEGRAM_SETUP.md) in full before continuing —
none of the rules will alert to Telegram until the global
`telegram_bot_token` / `telegram_room_id` / `indexer_connection` pillar
values are set on your manager.

## 6. Apply the Salt state

```bash
sudo salt-call state.apply elastalert -l info
```

Watch for errors referencing a specific rule filename — a YAML syntax error
or a missing enhancement module is the most common cause of a rule silently
not loading.

## 7. Verify the rules loaded

```bash
sudo docker logs so-elastalert --tail 100 -f
```

On startup, ElastAlert2 logs each rule it successfully loaded, e.g.:

```
INFO:elastalert:Loaded rule 'Critical - SSH Brute Force Authentication Attempt'
```

If a rule is missing from this list, check the log for a traceback right
above where it should have appeared.

## 8. Test each rule

See [`TESTING.md`](TESTING.md) for how to safely trigger each detection to
confirm the full pipeline (Elasticsearch match → PH-time enhancement →
Telegram message → indexed alert visible in SOC UI) actually works
end-to-end, without waiting for a real incident.

## Troubleshooting

- **Rule loads but never fires**: run
  `sudo docker exec -it so-elastalert elastalert-test-rule /opt/so/rules/elastalert/<file>.yaml`
  to dry-run the query against real data and see if it matches anything at
  all.
- **Fires in test but no Telegram message**: double-check
  `telegram_bot_token` / `telegram_room_id` in the pillar file and that the
  bot has been added to the target group. Test the token directly with
  `curl "https://api.telegram.org/bot<TOKEN>/getMe"`.
- **Fires and Telegram works, but nothing appears in SOC UI**: check
  `indexer_connection` credentials (`es_username` / `es_password`) — a wrong
  password fails silently in some ElastAlert2 versions; check
  `so-elastalert` logs for an Elasticsearch auth error.
