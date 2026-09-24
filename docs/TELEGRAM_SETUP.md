# Telegram Integration Setup

This describes how the ElastAlert2 → Telegram notification path is
configured on the Security Onion manager. **No secrets are committed to this
repository** — every value below is a placeholder you fill in on your own
server.

## 1. Create the bot and group

1. In Telegram, talk to **@BotFather** → `/newbot` → follow the prompts to
   get a bot token (looks like `123456789:AAExampleTokenDoNotCommitThis`).
2. Create (or reuse) a Telegram group for alert notifications and add the bot
   to it.
3. Get the group's chat ID (e.g. message
   `https://api.telegram.org/bot<TOKEN>/getUpdates` after posting a message
   in the group, or add a bot like `@RawDataBot` temporarily) — it will look
   like `-1001234567890`.

## 2. Configure ElastAlert2 (server-side, not in this repo)

Security Onion manages ElastAlert2 configuration through Salt pillar. On the
manager, the relevant file is:

```
/opt/so/saltstack/local/pillar/elastalert/soc_elastalert.sls
```

```yaml
elastalert:
  config:
    telegram_bot_token: "<YOUR_BOT_TOKEN>"        # from BotFather — keep secret
    telegram_room_id: "<YOUR_CHAT_ID>"             # target group chat ID
    indexer_connection:
      es_host: elasticsearch
      es_port: 9200
      es_username: so_elastic
      es_password: "<YOUR_ELASTIC_PASSWORD>"        # keep secret
      use_ssl: true
      verify_certs: false
      indexer_alerts_name: logs-detections.alerts-so
```

This file lives only on the manager (outside any git repo) or, if you do
version-control it, must be excluded via `.gitignore` and/or encrypted with
`git-crypt` / `sops` / Salt's own pillar encryption. **Never commit real
values for `telegram_bot_token` or `es_password`.**

After editing, apply the state so the `so-elastalert` container picks it up:

```bash
sudo salt-call state.apply elastalert -l info
# or, from the manager:
so-elastalert-restart
```

## 3. How rules use it

Individual rule files in [`../detection-rules/`](../detection-rules/) do
**not** contain the bot token or chat ID — they only reference the alerter
by name:

```yaml
alert:
  - telegram
  - indexer
telegram_msg_title: "🔴 CRITICAL - SSH Brute Force Detected"
alert_text: |
  ...
```

ElastAlert2 reads `telegram_bot_token` / `telegram_room_id` from the global
config above and applies them to every rule that lists `telegram` in its
`alert:` block. This means the credentials only need to be set once, on the
server, and every rule in this repo can be committed publicly without risk —
**with one exception**: some rules were originally exported with an inline
`indexer_connection` block that duplicates the global Elasticsearch
credentials. Those were stripped before committing (see
`detection-rules/port-scanning.yml` for an example) — always check a
freshly-pulled rule file for an `indexer_connection:` block containing
`es_password` before pushing it to GitHub.

## 4. Testing

```bash
# from the manager, dry-run a single rule without needing a real match:
sudo docker exec -it so-elastalert elastalert-test-rule /opt/so/rules/elastalert/rule1_ssh_bruteforce.yaml
```

A successful test prints the would-be Telegram message body to stdout
without actually sending it (unless `--alert` is passed).
