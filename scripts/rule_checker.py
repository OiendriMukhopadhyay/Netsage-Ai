"""
NetSage AI - Rule Checker
==========================
Deterministic (non-AI) checks for the six config-mistake categories called
out in the project spec:
  1. Duplicate IP addresses
  2. Wrong subnet masks
  3. Gateway mismatch (host gateway vs router interface IP)
  4. Interface administratively/operationally down
  5. Missing VLAN assignment (port not on the VLAN it should be)
  6. Missing routes (destination network absent from the routing table)

Two modes:
  A) STRUCTURED mode - runs the six check_* functions against clean,
     structured "device snapshot" data (data/device_snapshots.json).
     This is the ground-truth deterministic layer: same input always
     gives the same finding, with no AI involved.
  B) TEXT-SCAN mode - runs a lightweight keyword/regex pass over every
     row of data/cases.csv so the checker has *some* signal on all 36
     cases, not just the structured subset. This is intentionally
     simple and conservative (flags "possible" issues) since raw
     show-command text is unstructured.

Run:
    python3 rule_checker.py
Outputs:
    logs/rule_checker_structured_results.csv
    logs/rule_checker_textscan_results.csv
    Prints a summary to stdout (this IS the "sample output" deliverable;
    also saved to logs/rule_checker_sample_output.txt)
"""
import csv
import json
import os
import re
import sys
from ipaddress import ip_network, ip_interface

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
LOG_DIR = os.path.join(BASE, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


# ----------------------------------------------------------------------
# A) STRUCTURED, GENERIC DETERMINISTIC CHECKS
# ----------------------------------------------------------------------

def check_duplicate_ips(hosts):
    """hosts: list of {"name": str, "ip": str}. Returns list of finding dicts."""
    findings = []
    seen = {}
    for h in hosts:
        seen.setdefault(h["ip"], []).append(h["name"])
    for ip, names in seen.items():
        if len(names) > 1:
            findings.append({
                "check": "duplicate_ip",
                "severity": "high",
                "detail": f"IP {ip} is assigned to multiple devices: {', '.join(names)}"
            })
    return findings


def check_subnet_mask_mismatch(interfaces):
    """interfaces: list of {"name": str, "ip": str, "mask": str} on the same segment.
    Flags interfaces on the same link whose prefix length disagrees."""
    findings = []
    if len(interfaces) < 2:
        return findings
    prefixes = set()
    for i in interfaces:
        try:
            iface = ip_interface(f"{i['ip']}/{i['mask']}")
            prefixes.add(iface.network.prefixlen)
        except ValueError as e:
            findings.append({
                "check": "subnet_mask_mismatch",
                "severity": "high",
                "detail": f"{i['name']}: could not parse {i['ip']}/{i['mask']} ({e})"
            })
    if len(prefixes) > 1:
        detail = ", ".join(f"{i['name']}={i['ip']}/{i['mask']}" for i in interfaces)
        findings.append({
            "check": "subnet_mask_mismatch",
            "severity": "high",
            "detail": f"Mismatched prefix lengths on same segment: {detail}"
        })
    return findings


def check_gateway_mismatch(host_gateway, router_ip):
    findings = []
    if host_gateway != router_ip:
        findings.append({
            "check": "gateway_mismatch",
            "severity": "high",
            "detail": f"Host default gateway {host_gateway} does not match router interface IP {router_ip}"
        })
    return findings


def check_interface_down(interfaces):
    """interfaces: list of {"name": str, "admin_status": str, "line_status": str}"""
    findings = []
    for i in interfaces:
        if i.get("admin_status", "").lower() == "administratively down":
            findings.append({
                "check": "interface_down",
                "severity": "high",
                "detail": f"{i['name']} is administratively down (needs 'no shutdown')"
            })
        elif i.get("line_status", "").lower() not in ("up", ""):
            findings.append({
                "check": "interface_down",
                "severity": "medium",
                "detail": f"{i['name']} line protocol is {i['line_status']}"
            })
    return findings


def check_missing_vlan(port_name, configured_vlan, expected_vlan):
    findings = []
    if str(configured_vlan) != str(expected_vlan):
        findings.append({
            "check": "missing_vlan",
            "severity": "high",
            "detail": f"{port_name} is on VLAN {configured_vlan}, expected VLAN {expected_vlan}"
        })
    return findings


def check_missing_route(routing_table, destination_cidr):
    findings = []
    dest = ip_network(destination_cidr)
    covered = False
    for route in routing_table:
        try:
            net = ip_network(route)
        except ValueError:
            continue
        if dest.subnet_of(net) or dest == net:
            covered = True
            break
    if not covered:
        findings.append({
            "check": "missing_route",
            "severity": "high",
            "detail": f"No route in the routing table covers destination {destination_cidr}"
        })
    return findings


def run_structured_checks():
    snap_path = os.path.join(DATA_DIR, "device_snapshots.json")
    with open(snap_path) as f:
        snapshots = json.load(f)

    results = []
    for snap in snapshots:
        case_id = snap["case_id"]
        findings = []
        if "hosts_for_dup_check" in snap:
            findings += check_duplicate_ips(snap["hosts_for_dup_check"])
        if "interfaces_for_mask_check" in snap:
            findings += check_subnet_mask_mismatch(snap["interfaces_for_mask_check"])
        if "gateway_check" in snap:
            gc = snap["gateway_check"]
            findings += check_gateway_mismatch(gc["host_gateway"], gc["router_ip"])
        if "interfaces_for_down_check" in snap:
            findings += check_interface_down(snap["interfaces_for_down_check"])
        if "vlan_check" in snap:
            vc = snap["vlan_check"]
            findings += check_missing_vlan(vc["port_name"], vc["configured_vlan"], vc["expected_vlan"])
        if "route_check" in snap:
            rc = snap["route_check"]
            findings += check_missing_route(rc["routing_table"], rc["destination_cidr"])

        results.append({
            "case_id": case_id,
            "num_findings": len(findings),
            "findings": findings,
        })
    return results


# ----------------------------------------------------------------------
# B) TEXT-SCAN PASS OVER ALL 36 CASES (conservative keyword/regex heuristics)
# ----------------------------------------------------------------------

TEXT_RULES = [
    ("duplicate_ip",       re.compile(r"duplicate|conflict", re.I)),
    ("wrong_mask",         re.compile(r"subnet mask|/25 on host|255\.255\.255\.\d+ vs|mask mismatch|mask too specific", re.I)),
    ("gateway_mismatch",   re.compile(r"gateway.*(mismatch|does not match|blank|100\b)|default-router", re.I)),
    ("interface_down",     re.compile(r"administratively down|shutdown|half-duplex|input errors|CRC", re.I)),
    ("missing_vlan",       re.compile(r"VLAN ?1 \(default\)|not listed under VLAN|vlan mismatch|voice vlan: none", re.I)),
    ("missing_route",      re.compile(r"no route|not listed|missing route|no entries for|route to .* \(no", re.I)),
]


def run_textscan_checks():
    cases_path = os.path.join(DATA_DIR, "cases.csv")
    results = []
    with open(cases_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            blob = " ".join([row["symptom"], row["topology_note"], row["show_outputs"]])
            hits = [name for name, pattern in TEXT_RULES if pattern.search(blob)]
            results.append({
                "case_id": row["case_id"],
                "concept_tag": row["concept_tag"],
                "possible_issues": hits,
            })
    return results


# ----------------------------------------------------------------------
def main():
    structured = run_structured_checks()
    textscan = run_textscan_checks()

    # Write structured results
    with open(os.path.join(LOG_DIR, "rule_checker_structured_results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "check", "severity", "detail"])
        for r in structured:
            if not r["findings"]:
                w.writerow([r["case_id"], "none", "-", "No deterministic issues found"])
            for finding in r["findings"]:
                w.writerow([r["case_id"], finding["check"], finding["severity"], finding["detail"]])

    # Write textscan results
    with open(os.path.join(LOG_DIR, "rule_checker_textscan_results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "concept_tag", "possible_issues"])
        for r in textscan:
            w.writerow([r["case_id"], r["concept_tag"], ";".join(r["possible_issues"]) or "none"])

    # Sample output printed + saved
    lines = []
    lines.append("=" * 70)
    lines.append("NetSage AI Rule Checker - Sample Output")
    lines.append("=" * 70)
    lines.append("")
    lines.append("--- A) STRUCTURED deterministic checks (device_snapshots.json) ---")
    for r in structured:
        lines.append(f"\n[{r['case_id']}] {r['num_findings']} finding(s):")
        for finding in r["findings"]:
            lines.append(f"   - ({finding['severity'].upper()}) {finding['check']}: {finding['detail']}")
        if not r["findings"]:
            lines.append("   - No deterministic issues found")

    lines.append("\n" + "-" * 70)
    lines.append("--- B) TEXT-SCAN pass over all cases.csv rows (heuristic) ---")
    total_flagged = sum(1 for r in textscan if r["possible_issues"])
    lines.append(f"Flagged {total_flagged} / {len(textscan)} cases with at least one keyword match.\n")
    for r in textscan[:10]:
        lines.append(f"[{r['case_id']}] ({r['concept_tag']}): {', '.join(r['possible_issues']) or 'none'}")
    lines.append(f"... ({len(textscan) - 10} more rows in logs/rule_checker_textscan_results.csv)")

    output = "\n".join(lines)
    print(output)
    with open(os.path.join(LOG_DIR, "rule_checker_sample_output.txt"), "w") as f:
        f.write(output + "\n")


if __name__ == "__main__":
    main()
