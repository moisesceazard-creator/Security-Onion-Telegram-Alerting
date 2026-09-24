# Detection Rule Reference

All rules run inside `so-elastalert` (ElastAlert2) on the Security Onion
manager. All apply `PHTimeEnhancement` and alert via `telegram` + `indexer`.

| Rule file | Severity | ElastAlert type | Source index | ATT&CK | Trigger logic | Realert window |
|---|---|---|---|---|---|---|
| `ssh-bruteforce.yml` | 🔴 Critical | `any` | `logs-detections.alerts-so-*` | T1110 Brute Force / T1021.004 SSH | Fires on any `"Security Onion - Grid Node Login Failure (SSH)"` alert | 1 min |
| `phishing-malicious-ip.yml` | 🎣 High | `any` | `logs-suricata.alerts-so-*` | T1566 Phishing / T1204 User Execution | Fires on Suricata `"ET COMPROMISED Known Feodo C2 IP"` alert | 1 min |
| `unauthorized-access.yml` | 🟠 High | `frequency` | `logs-system.security-default-*` | T1078 Valid Accounts | ≥3 Windows logon-failure events (4625, logon type 2/7) from the same host in 5 min | 15 min |
| `port-scanning.yml` | 🟡 Medium | `cardinality` | `logs-zeek-so-*` | T1046 Network Service Discovery | A source IP touches >20 distinct destination ports in 5 min (internal noise/known IPs excluded) | 5 min |
| `removable-media.yml` | 🟠 High | `any` | `logs-windows.powershell-default-*` | T1052.001 Exfiltration Over Physical Medium: USB | Fires on the `UNAUTHORIZED_USB_STORAGE_CONFIRMED` marker in PowerShell process command-line logs | 1 min |
| `agent-uninstalled.yml` | 🔴 High | `any` | `.fleet-agents` | T1562.001 Impair Defenses | An Elastic Agent on a monitored endpoint becomes inactive/unenrolled | 5 min |
| `new-device.yml` *(disabled by default)* | 🟡 Medium | `new_term` | `logs-zeek-so-*` | T1078 / Initial Access surface | First-seen `source.ip` in the monitored `/23` in the last 7 days | 30 min |

## Notes

- **`new-device.yml`** is deployed under `elastalert_disabled/` on the
  server, meaning it exists but is not currently active. Move it to the
  enabled rules directory and re-apply the Salt state to turn it on.
- **Endpoint/IP values are environment-specific.** `agent-uninstalled.yml`
  hard-codes the monitored hostnames (`mis-pc2`, `mis-pc5`, ...) and
  `port-scanning.yml` / `new-device.yml` hard-code the internal subnet
  (`192.168.92.0/23`) and a short exclusion list of known-noisy internal
  hosts. Update these to match your own environment before reuse — they are
  intentionally environment-specific here, kept as-is for transparency about
  what was actually deployed and tested.
- **Severity mapping** (`event.severity` / `sigma_level`) mirrors Security
  Onion's native detection severity scale so alerts written by the `indexer`
  alerter sort and filter consistently with built-in detections in the SOC
  UI.
