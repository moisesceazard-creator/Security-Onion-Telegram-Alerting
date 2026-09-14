# 🛡️ Security Onion Near-Real-Time Alerting

> A Security Onion alerting architecture that delivers selected high-value security detections to Telegram through near-real-time automated notifications while preserving native alert visibility within the Security Onion SOC dashboard.

**Author:** Moises Ceazar Del Mundo  
**Deployment Context:** Security Onion SOC — Tanauan City Hall MIS Office  
**Focus:** SOC Engineering · Detection Engineering · Alert Automation · Security Monitoring

---

## 📖 Overview

Security Onion provides security monitoring and detection capabilities through components such as Suricata, Zeek, Elastic Agent, Elasticsearch, and ElastAlert2.

This project extends Security Onion's existing detection pipeline with a **near-real-time Telegram notification layer** for selected high-value security events.

Configured detections are automatically forwarded to a dedicated Telegram chat shortly after the detection is generated, while the same alert is preserved within Security Onion's native alert index for persistent SOC visibility.

> **Alert Latency:** The implementation uses ElastAlert2 polling rather than instantaneous event-driven delivery. Alerts are delivered within one polling cycle, typically around **1–3 minutes**, with a maximum expected delay of approximately **5 minutes** under the documented configuration.

---

## 🎯 Objectives

- Extend Security Onion's existing alerting capabilities.
- Provide near-real-time security notifications through Telegram.
- Develop custom ElastAlert2 detection rules for high-value security events.
- Maintain native Security Onion alert visibility.
- Convert UTC event timestamps to Philippine Time (UTC+8).
- Centralize sensitive credentials using Security Onion's secrets management mechanism.
- Improve analyst awareness and support faster security triage.

---

## 🏗️ Architecture

```text
┌──────────────────────────┐
│    Telemetry Sources     │
├──────────────────────────┤
│        Suricata          │
│          Zeek            │
│     Elastic Agent       │
│         Fleet            │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      Elasticsearch       │
│   Security Onion Data    │
│          Store           │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│       ElastAlert2        │
│ Detection & Alerting     │
│         Engine           │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│   Custom Detection       │
│         Rules            │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│   PH Time Enhancement    │
│       UTC → UTC+8        │
└────────────┬─────────────┘
             │
             ▼
       ┌───────────────┐
       │ Dual Dispatch │
       └───────┬───────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌──────────────┐ ┌──────────────────┐
│   Telegram   │ │ Native Alert     │
│ Notification │ │      Index       │
└──────┬───────┘ └────────┬─────────┘
       │                  │
       ▼                  ▼
┌──────────────┐ ┌──────────────────┐
│   Analyst    │ │ Security Onion   │
│    Chat      │ │ SOC Dashboard    │
└──────────────┘ └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │   SOC Cases      │
                  │ Investigation    │
                  └──────────────────┘
```

---

## 🚨 Detection Coverage

The implementation includes seven purpose-built detection rules:

| Detection Scenario | Purpose |
|---|---|
| **SSH/RDP Brute-Force** | Detect repeated authentication failures that may indicate credential-guessing activity. |
| **Phishing / Malicious IP** | Detect outbound connections to known malicious infrastructure. |
| **Unauthorized Workstation Access** | Detect repeated failed Windows logon or unlock attempts. |
| **Network Reconnaissance / Port Scanning** | Detect abnormal scanning behavior based on destination-port activity. |
| **Unauthorized Removable Media** | Detect confirmed USB storage device activity. |
| **New Device on LAN** | Detect previously unseen devices joining the network. |
| **Elastic Agent Uninstalled** | Detect removal or unenrollment of an endpoint monitoring agent. |

---

## ⚙️ Key Engineering Components

### 1. Custom ElastAlert2 Detection Rules

Seven purpose-built ElastAlert2 rules were developed for the monitored environment, covering:

- SSH brute-force detection
- Malicious IP detection
- Windows authentication failure detection
- Port scanning detection
- Unauthorized USB activity
- New device detection
- Elastic Agent removal detection

Each rule evaluates Security Onion telemetry stored in Elasticsearch and generates an alert when its configured detection conditions are satisfied.

### 2. Near-Real-Time Telegram Notification

The project uses ElastAlert2's polling-based alerting mechanism to forward matched detections to Telegram.

```text
Security Event
      ↓
Elasticsearch
      ↓
ElastAlert2 Polling
      ↓
Detection Match
      ↓
Telegram Alert
      ↓
Analyst Notification
```

Because the system uses polling rather than instantaneous event-driven delivery, notification latency depends on the polling cycle.

```text
Typical: ~1–3 minutes
Maximum expected: ~5 minutes per polling cycle
```

This is therefore described as **near-real-time alerting**, rather than instantaneous real-time alerting.

### 3. Philippine Time Enhancement

A custom enhancement converts matched event timestamps from UTC to **Philippine Time (UTC+8)** before the event is rendered in the Telegram notification.

```text
UTC Event Timestamp
        ↓
PH Time Enhancement
        ↓
Philippine Time (UTC+8)
        ↓
Telegram Notification
```

### 4. Dual Alert Dispatch

Configured detections can use two alerting mechanisms:

```yaml
alert:
  - telegram
  - indexer
```

**Telegram**
- Near-real-time analyst notification
- Mobile-friendly alert delivery
- Faster awareness of high-value events

**Indexer**
- Writes the detection into Security Onion's native alert index
- Maintains persistent alert visibility
- Keeps the event available within the SOC dashboard

### 5. Native Security Onion Alert Integration

A custom indexer alerter writes matched detection events into:

```text
logs-detections.alerts-so
```

This allows alerts to remain visible within the SOC's normal investigation workflow.

### 6. Centralized Secrets Management

Sensitive credentials such as Telegram bot credentials and Elasticsearch authentication information are managed through Security Onion's centralized Salt pillar-based secrets mechanism.

This avoids unnecessarily hardcoding credentials into individual detection rule files.

---

## 🔍 SOC Alert Workflow

```text
Telemetry Sources
       ↓
Elasticsearch
       ↓
ElastAlert2
       ↓
Detection Rule Match
       ↓
PH Time Enhancement
       ↓
Dual Alert Dispatch
       ↓
 ┌─────┴─────┐
 ▼           ▼
Telegram    Native Index
 ▼           ▼
Analyst     SOC Dashboard
Notification    ↓
            Investigation
                ↓
             SOC Case
```

This allows analysts to receive a notification through Telegram while maintaining the detection inside the Security Onion SOC environment.

---

## 📩 Example Alert

A sample SSH brute-force notification follows this structure:

```text
🔴 CRITICAL - SSH Brute Force Detected

🚨 SSH Brute Force Authentication Attempt Detected!

📌 ATT&CK: T1110 - Brute Force /
T1021.004 - SSH

📋 Rule Matched:
Security Onion - Grid Node Login Failure (SSH)

🖥️ Attacker IP: 203.0.113.99
🎯 Target: mis-so
👤 User Attempted: administrator

🕐 Time (PH Time):
2026-09-14 13:00:47

⚡ Action:
Block source IP immediately, check for successful logins,
and review SSH logs.

📣 Notify:
MIS Department Head + IT Admin — URGENT
```

The same detection is also written to Security Onion's native alert index for dashboard-based investigation.

---

## 🧪 Testing & Validation

Testing focused on confirming that:

- Detection rules correctly matched relevant events.
- ElastAlert2 generated alerts when conditions were satisfied.
- Telegram notifications were successfully delivered.
- Alert timestamps were converted to Philippine Time.
- Alerts were simultaneously indexed within Security Onion.
- Alert information remained available in the SOC dashboard.
- Multiple detection scenarios could use the same alerting architecture.

---

## 🧰 Technologies Used

| Technology | Role |
|---|---|
| **Security Onion** | SOC monitoring and security operations platform |
| **Suricata** | Network intrusion detection |
| **Zeek** | Network security monitoring and metadata collection |
| **Elastic Agent** | Endpoint telemetry collection |
| **Elasticsearch** | Security event storage and search |
| **ElastAlert2** | Detection and alert automation |
| **Telegram Bot API** | Near-real-time analyst notification |
| **Salt Pillar** | Centralized secrets management |
| **Python** | Custom enhancement and alerting components |
| **YAML** | Detection rule configuration |

---

## 🧠 Design Decisions

### Why Telegram?

Telegram provides a lightweight and accessible mechanism for delivering security alerts to analysts without requiring an enterprise messaging platform.

### Why Near-Real-Time Instead of Real-Time?

The implementation relies on **ElastAlert2 polling**, meaning alerts are evaluated at polling intervals rather than being pushed instantaneously when an event enters Elasticsearch.

Using the term **near-real-time** accurately reflects the alert delivery behavior.

### Why Dual Dispatch?

Telegram provides fast analyst awareness, while Security Onion's native alert index provides persistent and queryable alert records.

Using both prevents the alerting workflow from depending entirely on either Telegram or the SOC dashboard.

### Why PH Time Enhancement?

Converting timestamps from UTC to Philippine Time makes alerts immediately actionable for analysts operating in the Philippines.

### Why Cardinality-Based Port Scanning Detection?

Port scanning is primarily a behavioral pattern rather than a single packet signature. A cardinality-based approach can identify a source interacting with an unusually large number of destination ports within a defined period.

---

## 🔐 Security Considerations

This project was developed in a controlled laboratory and academic SOC environment.

Sensitive information must **never be committed to a public GitHub repository**, including:

- Telegram bot tokens
- Elasticsearch credentials
- Passwords
- API keys
- Private IP information where disclosure is inappropriate

Configuration files and screenshots should be reviewed and sanitized before publication.

---

## 📈 Project Outcome

The project extended Security Onion's existing detection capabilities with a centralized, near-real-time notification mechanism.

The resulting architecture provides:

- Custom security detection rules
- Automated alert generation
- Near-real-time Telegram notification
- Philippine Time alert timestamps
- Native Security Onion alert indexing
- Persistent SOC dashboard visibility
- Centralized secrets management
- A foundation for additional detection and response automation

---

## 📚 Skills Demonstrated

- SOC Engineering
- Detection Engineering
- Security Monitoring
- Alert Automation
- SIEM Operations
- Network Security Monitoring
- Endpoint Telemetry
- Elasticsearch
- ElastAlert2
- Security Onion
- Suricata
- Zeek
- Python
- YAML Configuration
- Incident Detection
- Security Alert Integration

---

## 👤 Author

**Moises Ceazar Del Mundo**

Bachelor of Science in Information Technology  
Major in Information Security  
De La Salle Lipa

---

> **Note:** This project was developed for educational, laboratory, and cybersecurity portfolio purposes. Indicators, IP addresses, hostnames, and other environment-specific values should be treated as lab/training data unless explicitly identified otherwise.
