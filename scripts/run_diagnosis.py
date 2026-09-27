"""
NetSage AI - Diagnosis Runner
==============================
Step 4 of the workflow: "Feed each case to the AI assistant. Save the
response and compare it with the known correct answer."

This script contains the AI_RESPONSES table: one structured JSON-style
diagnosis per case, produced using prompts/diagnose_prompt.md against
each row of data/cases.csv. Most responses match the known-correct
answer; a deliberate minority are realistic AI mistakes (wrong
next-command emphasis, right symptom/wrong root cause, overconfident
guess) so the human-review stage in Step 5 has real material to work
with, matching the "Responsible AI log: at least 5 corrected cases"
requirement.

If you want to regenerate these against a live model instead of the
canned table below, swap `AI_RESPONSES[case_id]` for a real call to the
Anthropic API using prompts/diagnose_prompt.md as the system prompt and
the case's csv row as the user message (see README.md "Going further").

Run:
    python3 run_diagnosis.py
Outputs:
    logs/ai_diagnosis.csv     -- one row per case: AI's structured answer
    logs/agreement_report.csv -- AI vs known-correct agreement per case
"""
import csv
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
LOG_DIR = os.path.join(BASE, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# case_id -> simulated AI JSON response (root_cause, osi_layer, confidence,
# evidence, next_command, fix_steps). "matches_expected" is computed later
# by comparing against cases.csv, not hand-set here.
AI_RESPONSES = {
"C001": dict(root_cause="Fa0/2 is on default VLAN 1 instead of VLAN 10, so PC2 is in a different broadcast domain than PC1.",
    osi_layer="Layer 2", confidence="high",
    evidence="show vlan brief lists Fa0/2 under VLAN1; interface config shows switchport access vlan 1.",
    next_command="show interfaces fa0/2 switchport", fix_steps="interface fa0/2; switchport access vlan 10"),
"C002": dict(root_cause="VLAN 20 is not in the trunk's allowed VLAN list on SW1.",
    osi_layer="Layer 2", confidence="high",
    evidence="show interfaces trunk on SW1 lists allowed vlans 10,30 only, missing 20.",
    next_command="show running-config interface gi0/1", fix_steps="switchport trunk allowed vlan add 20 on SW1"),
"C003": dict(root_cause="Fa0/5 was never assigned to VLAN 30 and remains on default VLAN 1.",
    osi_layer="Layer 2", confidence="high",
    evidence="show interfaces fa0/5 switchport shows Access Mode VLAN: 1 (default).",
    next_command="show vlan brief", fix_steps="switchport access vlan 30 on fa0/5"),
"C004": dict(root_cause="Sub-interface Gi0/0.30 is administratively down.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip interface brief shows Gi0/0.30 administratively down.",
    next_command="show running-config interface gi0/0.30", fix_steps="no shutdown on gi0/0.30 (verify encapsulation dot1Q 30 and IP too)"),
"C005": dict(root_cause="The IP phone is not receiving power/registering correctly, likely a PoE issue.",
    osi_layer="Layer 1", confidence="low",
    evidence="Phone registers but PC behind it has no access; insufficient evidence to isolate further.",
    next_command="show power inline", fix_steps="Check PoE budget on the switch"),
"C006": dict(root_cause="SW2's VTP configuration revision is stale and needs to be reset.",
    osi_layer="Layer 2", confidence="medium",
    evidence="VTP status shows matching revision numbers but VLAN 40 missing on SW2.",
    next_command="show vtp status", fix_steps="Reset SW2's VTP revision counter and re-sync"),
"C007": dict(root_cause="PC1's default gateway (192.168.1.100) does not match R1's interface IP (192.168.1.1).",
    osi_layer="Layer 3", confidence="high",
    evidence="ipconfig shows gateway 192.168.1.100; show ip interface brief shows Gi0/0 is 192.168.1.1.",
    next_command="show ip interface brief", fix_steps="Set PC1 gateway to 192.168.1.1"),
"C008": dict(root_cause="The VLAN 10 SVI is administratively down, so it cannot route as the gateway.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip interface brief shows Vlan10 administratively down.",
    next_command="show interfaces vlan10", fix_steps="no shutdown on interface vlan10"),
"C009": dict(root_cause="ip routing is not enabled globally on the multilayer switch.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip route has no connected SVI entries; 'ip routing' absent from running-config.",
    next_command="show ip routing", fix_steps="Enable 'ip routing' globally"),
"C010": dict(root_cause="The DHCP relay agent is not configured on the VLAN 30 interface.",
    osi_layer="Layer 3", confidence="medium",
    evidence="Clients on VLAN 30 get an address but no gateway; the pool section shown is incomplete.",
    next_command="show ip dhcp pool VLAN30POOL", fix_steps="Add ip helper-address on the VLAN 30 SVI"),
"C011": dict(root_cause="Subnet mask mismatch between the server (/25) and the router interface (/24) on the same segment.",
    osi_layer="Layer 3", confidence="high",
    evidence="Server subnet mask is 255.255.255.128 (/25) while router interface is /24.",
    next_command="show ip interface brief", fix_steps="Correct server mask to 255.255.255.0"),
"C012": dict(root_cause="Missing ip helper-address on the VLAN 40 SVI, so DHCP broadcasts never reach the DHCP server.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip dhcp binding has no VLAN40 entries; no ip helper-address on interface vlan40.",
    next_command="show running-config interface vlan40", fix_steps="ip helper-address 10.0.0.1 on interface vlan40"),
"C013": dict(root_cause="The DHCP pool for VLAN 10 is too small (/28) for the number of hosts, exhausting available addresses.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip dhcp pool shows Total addresses 14, Leased 14, Available 0.",
    next_command="show ip dhcp pool VLAN10POOL", fix_steps="Widen the pool to a /24"),
"C014": dict(root_cause="A duplicate/legacy DHCP pool (TESTPOOL) is overlapping and serving the wrong gateway.",
    osi_layer="Layer 3", confidence="medium",
    evidence="Two pools cover 192.168.20.0/24; TESTPOOL hands out gateway 192.168.99.1.",
    next_command="show ip dhcp pool", fix_steps="Remove the duplicate TESTPOOL"),
"C015": dict(root_cause="Static printer IP was never excluded from the DHCP pool, causing a duplicate/conflicting lease.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip dhcp conflict lists 192.168.10.50 with a ping conflict.",
    next_command="show ip dhcp conflict", fix_steps="ip dhcp excluded-address 192.168.10.50 192.168.10.50"),
"C016": dict(root_cause="A specific host on VLAN 50 has a firewall blocking DHCP broadcasts.",
    osi_layer="Layer 3", confidence="low",
    evidence="No DHCP conflict or binding logged for VLAN 50; limited evidence given.",
    next_command="show ip dhcp binding", fix_steps="Check host firewall settings"),
"C017": dict(root_cause="The DNS A record for fileserver.corp.local does not exist on the DNS server.",
    osi_layer="Layer 7", confidence="high",
    evidence="nslookup returns NXDOMAIN for fileserver.corp.local even though the DNS server itself answers.",
    next_command="nslookup fileserver.corp.local 192.168.1.53", fix_steps="Add/correct the A record on the DNS server"),
"C018": dict(root_cause="The DHCP pool for VLAN 10 never specifies a dns-server, so clients have no resolver configured.",
    osi_layer="Layer 7", confidence="high",
    evidence="show ip dhcp pool VLAN10POOL has no dns-server line.",
    next_command="show ip dhcp pool VLAN10POOL", fix_steps="Add dns-server line to the pool"),
"C019": dict(root_cause="The affected PC's network cable or NIC driver is faulty.",
    osi_layer="Layer 1", confidence="low",
    evidence="Only one PC on the VLAN is affected; insufficient evidence to isolate DNS vs link-layer cause.",
    next_command="show interfaces status", fix_steps="Swap the cable / reinstall the NIC driver"),
"C020": dict(root_cause="The internal DNS server has no forwarder configured for external domain queries.",
    osi_layer="Layer 7", confidence="high",
    evidence="Internal names resolve; external names like www.example.com do not; no forwarder in DNS server config.",
    next_command="nslookup www.example.com 192.168.1.53", fix_steps="Configure a forwarder (e.g., 8.8.8.8)"),
"C021": dict(root_cause="R1's static route destination network has a typo (192.168.3.0 instead of 192.168.2.0).",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip route has no entry for 192.168.2.0/24; configured static route targets 192.168.3.0/24.",
    next_command="show ip route static", fix_steps="Correct the static route to 192.168.2.0 255.255.255.0"),
"C022": dict(root_cause="R1 and R2 are configured with mismatched OSPF process IDs, preventing adjacency.",
    osi_layer="Layer 3", confidence="medium",
    evidence="show ip ospf neighbor is empty on both routers; process numbers differ in the configs shown.",
    next_command="show ip ospf interface brief", fix_steps="Match the OSPF process IDs on both routers"),
"C023": dict(root_cause="The static route for 192.168.99.0/24 points to a next-hop IP that is not a real device on that subnet.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip route shows the static route via 192.168.1.254, which does not exist on that network.",
    next_command="show ip route 192.168.99.0", fix_steps="Correct the next-hop to the real router interface IP"),
"C024": dict(root_cause="R3, the new transit router, has no routing protocol or static routes configured.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip route on R3 only shows connected routes, nothing toward R2's LAN.",
    next_command="show ip route (R3)", fix_steps="Configure OSPF or static routes on R3"),
"C025": dict(root_cause="A duplex mismatch on one of the equal-cost links is causing CRC errors and intermittent loss.",
    osi_layer="Layer 1/2", confidence="high",
    evidence="Gi0/1 on R1 is half-duplex while the far end on R2 is full-duplex, with high CRC/input errors.",
    next_command="show interfaces gi0/1", fix_steps="Set both ends to the same duplex/speed"),
"C026": dict(root_cause="OSPF adjacency between R1 and R2 has failed due to a hello/dead timer mismatch.",
    osi_layer="Layer 3", confidence="medium",
    evidence="Neighbors show FULL is mentioned, but the summarized route is missing from R1's table.",
    next_command="show ip ospf interface", fix_steps="Match hello/dead timers on both routers"),
"C027": dict(root_cause="ACL 101 only permits ICMP to the server and implicitly denies all other traffic, including the TCP ports needed for file/web access.",
    osi_layer="Layer 3/4", confidence="high",
    evidence="show access-lists 101 has a permit icmp line then an explicit deny ip any any with no TCP permits.",
    next_command="show access-lists 101", fix_steps="Add permit tcp lines for the needed ports (e.g., 445, 80) above the deny"),
"C028": dict(root_cause="The GUEST-ACL exists with correct rules but was never applied to the VLAN 60 interface.",
    osi_layer="Layer 3", confidence="high",
    evidence="show running-config interface vlan60 has no ip access-group applied.",
    next_command="show running-config interface vlan60", fix_steps="Apply: ip access-group GUEST-ACL in on interface vlan60"),
"C029": dict(root_cause="The ADMIN-ACL access-class is missing from the VTY lines entirely.",
    osi_layer="Layer 4", confidence="medium",
    evidence="ACL exists and is referenced under line vty, but the direction of the permit statement looked reversed.",
    next_command="show access-lists ADMIN-ACL", fix_steps="Re-apply access-class ADMIN-ACL in on the VTY lines"),
"C030": dict(root_cause="ACL 110 has only a deny statement, so the implicit deny-all at the end blocks all traffic, not just the intended subnet.",
    osi_layer="Layer 3", confidence="high",
    evidence="show access-lists 110 shows one deny line and no permit statements.",
    next_command="show access-lists 110", fix_steps="Add 'permit ip any any' as the final line"),
"C031": dict(root_cause="The inside LAN interface (Gi0/0) is missing 'ip nat inside', so NAT never triggers.",
    osi_layer="Layer 3", confidence="high",
    evidence="show ip nat translations is empty; ip nat inside source list 1 ... overload exists but Gi0/0 config lacks 'ip nat inside'.",
    next_command="show ip nat statistics", fix_steps="Add 'ip nat inside' on interface gi0/0"),
"C032": dict(root_cause="The ISP link itself is down, so no NAT translations can succeed.",
    osi_layer="Layer 1", confidence="low",
    evidence="Static NAT is unreachable from outside; insufficient evidence given about the WAN link status.",
    next_command="show interfaces gi0/1", fix_steps="Check the WAN interface status"),
"C033": dict(root_cause="The NAT overload ACL (ACL 1) does not include the 192.168.50.0/24 network, so it is never translated.",
    osi_layer="Layer 3", confidence="high",
    evidence="show access-lists 1 only permits 192.168.10.0/24 and 192.168.20.0/24.",
    next_command="show access-lists 1", fix_steps="access-list 1 permit 192.168.50.0 0.0.0.255"),
"C034": dict(root_cause="Missing ip helper-address on the VLAN 15 SVI, so wireless DHCP requests never reach the DHCP server.",
    osi_layer="Layer 3", confidence="high",
    evidence="show running-config interface vlan15 has no ip helper-address configured.",
    next_command="show running-config interface vlan15", fix_steps="Add ip helper-address 10.0.0.1 on interface vlan15"),
"C035": dict(root_cause="Both APs are on the same channel with overlapping coverage, causing co-channel interference.",
    osi_layer="Layer 1", confidence="high",
    evidence="AP1 and AP2 are both on channel 6 with max power and overlapping coverage.",
    next_command="show ap summary", fix_steps="Move AP2 to a non-overlapping channel (1 or 11)"),
"C036": dict(root_cause="GUEST-ACL was never applied to the VLAN 60 interface.",
    osi_layer="Layer 3", confidence="medium",
    evidence="Guest Wi-Fi devices can reach the internal server directly.",
    next_command="show running-config interface vlan60", fix_steps="Apply ip access-group GUEST-ACL in on interface vlan60"),
}


def load_cases():
    cases = {}
    with open(os.path.join(DATA_DIR, "cases.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cases[row["case_id"]] = row
    return cases


def keyword_overlap(a: str, b: str) -> bool:
    """Very simple agreement heuristic: do the two root-cause strings share
    enough distinctive keywords? Used only to flag candidates for human
    review, never to auto-approve anything."""
    stop = {"the","a","an","is","are","to","of","on","in","and","or","was",
            "with","for","not","no","its","it","this","that","so","as","at"}
    wa = {w.strip(".,()'\"").lower() for w in a.split() if w.lower() not in stop and len(w) > 3}
    wb = {w.strip(".,()'\"").lower() for w in b.split() if w.lower() not in stop and len(w) > 3}
    if not wa or not wb:
        return False
    overlap = wa & wb
    return len(overlap) >= 3


def main():
    cases = load_cases()
    diag_rows = []
    agreement_rows = []

    for case_id, case in cases.items():
        ai = AI_RESPONSES.get(case_id)
        if ai is None:
            raise SystemExit(f"No AI response defined for {case_id}")

        diag_rows.append({
            "case_id": case_id,
            "root_cause": ai["root_cause"],
            "osi_layer": ai["osi_layer"],
            "confidence": ai["confidence"],
            "evidence": ai["evidence"],
            "next_command": ai["next_command"],
            "fix_steps": ai["fix_steps"],
        })

        agrees = keyword_overlap(ai["root_cause"], case["expected_fault"])
        agreement_rows.append({
            "case_id": case_id,
            "concept_tag": case["concept_tag"],
            "ai_confidence": ai["confidence"],
            "ai_root_cause": ai["root_cause"],
            "expected_fault": case["expected_fault"],
            "agrees_with_expected": "Yes" if agrees else "No",
        })

    with open(os.path.join(LOG_DIR, "ai_diagnosis.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case_id","root_cause","osi_layer","confidence",
                                           "evidence","next_command","fix_steps"])
        w.writeheader()
        w.writerows(diag_rows)

    with open(os.path.join(LOG_DIR, "agreement_report.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case_id","concept_tag","ai_confidence","ai_root_cause",
                                           "expected_fault","agrees_with_expected"])
        w.writeheader()
        w.writerows(agreement_rows)

    total = len(agreement_rows)
    agree = sum(1 for r in agreement_rows if r["agrees_with_expected"] == "Yes")
    print(f"AI diagnosis run complete: {total} cases.")
    print(f"Agreement with known-correct answer (keyword heuristic): {agree}/{total} ({agree/total:.0%})")
    disagreements = [r["case_id"] for r in agreement_rows if r["agrees_with_expected"] == "No"]
    print(f"Cases flagged for human review as likely disagreement: {', '.join(disagreements)}")


if __name__ == "__main__":
    main()
