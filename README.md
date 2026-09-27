# NetSage AI — AI-Assisted Network Troubleshooting

NetSage AI is a networking troubleshooting project that combines **AI-assisted diagnosis**, **deterministic rule-based validation**, and **human review** to analyze common network configuration faults.

The project is designed around a simple principle: **AI can assist with diagnosis, but a human remains responsible for validating the result before action is taken.**

## Key Features

- 36 structured networking troubleshooting cases
- 8 fault categories: VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, and Wireless
- Evidence-based AI diagnosis using show-command/configuration output
- Deterministic rule checker for common configuration mistakes
- Human review workflow with Accepted / Edited / Rejected outcomes
- Responsible-AI log documenting cases where human review corrected the AI
- Excel dashboard for diagnosis, review, severity, and agreement analysis
- Packet Tracer example file
- Demo video and ready-to-follow demo script
- Reproducible offline pipeline using Python

## Project Workflow

```text
Network Case / Device Evidence
            │
            ▼
     Structured Prompt
            │
      ┌─────┴─────┐
      ▼           ▼
 AI Diagnosis   Rule Checker
      │           │
      └─────┬─────┘
            ▼
      Human Review
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
  Accepted Edited Rejected
            │
            ▼
   Logs + Agreement Report
            │
            ▼
        Dashboard
```

## Repository Structure

```text
NetSage-AI/
├── README.md
├── LICENSE
├── .gitignore
├── data/
│   ├── cases.csv
│   ├── cases_extra.json
│   └── device_snapshots.json
├── prompts/
│   ├── diagnose_prompt.md
│   └── explain_fix_prompt.md
├── scripts/
│   ├── build_cases.py
│   ├── build_dashboard.py
│   ├── build_review_log.py
│   ├── merge_extra_fields.py
│   ├── rule_checker.py
│   └── run_diagnosis.py
├── logs/
│   ├── ai_diagnosis.csv
│   ├── agreement_report.csv
│   ├── human_review_log.csv
│   ├── responsible_ai_log.md
│   ├── rule_checker_sample_output.txt
│   ├── rule_checker_structured_results.csv
│   └── rule_checker_textscan_results.csv
├── dashboard/
│   └── dashboard.xlsx
├── packet_tracer/
│   └── netsage_C007_gateway_mismatch.pkt
├── demo/
│   └── netsage_demo.mp4
└── docs/
    └── demo_video_script.md
```

## Case Coverage

The project contains **36 cases**, exceeding the minimum 30-case requirement, across eight network fault categories:

- VLAN
- Gateway
- DHCP
- DNS
- Routing
- ACL
- NAT
- Wireless

## Human Oversight

Human review is part of the core workflow rather than an optional step. The review log records three possible outcomes:

- **Accepted** — the AI diagnosis was considered correct.
- **Edited** — the reviewer modified the AI diagnosis.
- **Rejected** — the AI diagnosis was not accepted.

The responsible-AI log records examples where human review corrected the AI output and explains the reason for the correction.

## Deterministic Rule Checker

`scripts/rule_checker.py` performs rule-based checks independently of the AI. The current checks cover configuration issues such as:

- Duplicate IP addresses
- Incorrect subnet masks
- Gateway mismatches
- Down interfaces
- Missing VLANs
- Missing routes

This provides a second validation layer that does not depend on an AI model.

## Dashboard

`dashboard/dashboard.xlsx` summarizes the project results, including issue categories, severity, review outcomes, and AI agreement information.

## Run the Project

Python 3 is recommended.

From the repository root:

```bash
python scripts/build_cases.py
python scripts/rule_checker.py
python scripts/run_diagnosis.py
python scripts/build_review_log.py
python scripts/build_dashboard.py
```

The scripts generate or refresh the datasets and reports under `data/`, `logs/`, and `dashboard/`.

## Demo

A demo video is included at:

```text
demo/netsage_demo.mp4
```

The recording guide and storyboard are available at:

```text
docs/demo_video_script.md
```

The Packet Tracer example is available at:

```text
packet_tracer/netsage_C007_gateway_mismatch.pkt
```

## AI Implementation Note

The current `scripts/run_diagnosis.py` uses a predefined response table so that the complete workflow can run offline and reproducibly. This makes the project easy to demonstrate without requiring an API key.

For a live AI integration, the diagnosis step can be replaced with an API-based model call while keeping the downstream agreement report, human review, responsible-AI log, and dashboard workflow.

## Responsible AI

NetSage AI is designed as a decision-support system, not an autonomous network-change system. Diagnoses should be checked against the available evidence and reviewed by a human before network configuration changes are made.

## Project Status

**GitHub-ready project:** Yes

The repository includes source code, datasets, prompts, logs, dashboard, documentation, demo material, Packet Tracer material, a license, and GitHub-specific configuration.
