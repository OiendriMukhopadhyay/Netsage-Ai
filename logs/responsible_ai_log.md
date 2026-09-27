# NetSage AI — Responsible AI Log

Total cases reviewed: 36. Accepted: 26 | Edited: 5 | Rejected: 5.

**10 cases required a human correction to the AI's diagnosis** (minimum required: 5). Each is documented below.

---

## C005 — Rejected (VLAN)

**AI said:** The IP phone is not receiving power/registering correctly, likely a PoE issue.

**Human correction:** Root cause is a missing voice VLAN configuration on Fa0/3 (switchport voice vlan 110 never applied), not a PoE/power issue.

**Why the AI was wrong / what a reviewer should watch for:** AI had almost no interface/power evidence to work with and guessed PoE. It should have asked for 'show interfaces fa0/3 switchport' before proposing a cause, and its own confidence should have been lower than it stated.

**Reviewed by:** J. Alvarez

---

## C006 — Edited (VLAN)

**AI said:** SW2's VTP configuration revision is stale and needs to be reset.

**Human correction:** Root cause is that SW2 did not receive the VTP update because the trunk link was down at the time of the change, not a stale revision counter.

**Why the AI was wrong / what a reviewer should watch for:** AI focused on the revision number match and suggested resetting VTP, which would not fix a trunk-availability problem and risks wiping the VLAN database unnecessarily. Reviewer redirected the fix to checking trunk state first.

**Reviewed by:** J. Alvarez

---

## C010 — Edited (Gateway)

**AI said:** The DHCP relay agent is not configured on the VLAN 30 interface.

**Human correction:** Root cause is a missing 'default-router' line inside the DHCP pool itself, not a missing DHCP relay/helper-address (R1 IS the DHCP server here, one hop away, no relay is needed).

**Why the AI was wrong / what a reviewer should watch for:** AI defaulted to its most common DHCP pattern (missing helper-address) without checking that the DHCP server is local to the VLAN in this topology, so a relay was never the issue.

**Reviewed by:** M. Chen

---

## C016 — Rejected (DHCP)

**AI said:** A specific host on VLAN 50 has a firewall blocking DHCP broadcasts.

**Human correction:** Root cause is 'no service dhcp' globally disabling the DHCP process on the router, confirmed by the missing 'service dhcp' line in the running-config.

**Why the AI was wrong / what a reviewer should watch for:** AI's confidence was correctly marked low, but it guessed a single-host firewall issue when the symptom (NO PC in the VLAN gets an address) pointed to a router-wide DHCP outage. Reviewer used the next_command it should have asked for.

**Reviewed by:** M. Chen

---

## C019 — Rejected (DNS)

**AI said:** The affected PC's network cable or NIC driver is faulty.

**Human correction:** Root cause is the PC's DNS server statically set to 127.0.0.1 (itself) instead of the real DNS server 192.168.1.53.

**Why the AI was wrong / what a reviewer should watch for:** AI jumped to a Layer 1 cable/driver explanation without requesting 'ipconfig /all', which was the single most useful piece of evidence and was available in the case data.

**Reviewed by:** J. Alvarez

---

## C022 — Edited (Routing)

**AI said:** R1 and R2 are configured with mismatched OSPF process IDs, preventing adjacency.

**Human correction:** Root cause is an OSPF area mismatch (R1 advertises area 0, R2 advertises area 1 for the same link), not a process ID mismatch.

**Why the AI was wrong / what a reviewer should watch for:** Process IDs are locally significant and don't need to match between routers; the AI cited the wrong OSPF parameter. The area mismatch shown in the running-config is the actual blocker.

**Reviewed by:** M. Chen

---

## C025 — Edited (Routing)

**AI said:** A duplex mismatch on one of the equal-cost links is causing CRC errors and intermittent loss.

**Human correction:** Same root cause (duplex mismatch); edited only to add that BOTH ends should be set to the same fixed duplex/speed rather than assuming auto-negotiation will fix it, since auto/manual mismatches are the most common real-world cause of this exact symptom.

**Why the AI was wrong / what a reviewer should watch for:** Not wrong, just underspecified. Reviewer added the practical detail before sign-off.

**Reviewed by:** J. Alvarez

---

## C026 — Rejected (Routing)

**AI said:** OSPF adjacency between R1 and R2 has failed due to a hello/dead timer mismatch.

**Human correction:** Root cause is the OSPF area range mask on the ABR (R2) being /24 instead of the intended /22, so the summary doesn't cover all subordinate subnets.

**Why the AI was wrong / what a reviewer should watch for:** AI invented a hello/dead timer mismatch that isn't supported by any evidence in the case; neighbors were already stated as FULL, which rules out a timer problem entirely.

**Reviewed by:** J. Alvarez

---

## C029 — Edited (ACL)

**AI said:** The ADMIN-ACL access-class is missing from the VTY lines entirely.

**Human correction:** Root cause is that the ADMIN-ACL entry has source and destination reversed (matches traffic sourced from port 22, not destined to port 22), not a missing access-class.

**Why the AI was wrong / what a reviewer should watch for:** AI's evidence field actually noticed the direction problem but then wrote a root_cause about the access-class being 'missing,' which contradicts its own evidence citation. Reviewer corrected the root_cause to match the evidence.

**Reviewed by:** M. Chen

---

## C032 — Rejected (NAT)

**AI said:** The ISP link itself is down, so no NAT translations can succeed.

**Human correction:** Root cause is a wrong internal port in the static NAT mapping (8080 configured, server listens on 80), not a WAN link outage.

**Why the AI was wrong / what a reviewer should watch for:** Case data explicitly stated the WAN/ISP link was fine ('works internally'); AI ignored that detail and proposed checking the WAN interface, which had already been ruled out by the topology note.

**Reviewed by:** M. Chen

---
