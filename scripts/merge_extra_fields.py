"""
Adds the AI-diagnosis + human-review columns onto data/cases.csv so it
matches the column layout the user supplied as an example:

case_id, issue_type, symptom, topology_note, show_outputs, expected_fault,
osi_layer, concept_tag, severity, ai_root_cause, ai_confidence,
evidence_reference, next_command, proposed_fix, human_review, reviewer_note

Pulls from files already built in this project:
  data/cases.csv          -> case_id, symptom, topology_note, show_output,
                              expected_fault, osi_layer, concept_tag, severity
  logs/ai_diagnosis.csv   -> ai_root_cause, ai_confidence, evidence_reference,
                              next_command, proposed_fix
  logs/human_review_log.csv -> human_review, reviewer_note
"""
import csv
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
LOG_DIR = os.path.join(BASE, "logs")


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["case_id"]: r for r in csv.DictReader(f)}


def main():
    cases = load_csv(os.path.join(DATA_DIR, "cases.csv"))
    ai = load_csv(os.path.join(LOG_DIR, "ai_diagnosis.csv"))
    review = load_csv(os.path.join(LOG_DIR, "human_review_log.csv"))

    fieldnames = ["case_id", "issue_type", "symptom", "topology_note", "show_outputs",
                  "expected_fault", "osi_layer", "concept_tag", "severity",
                  "ai_root_cause", "ai_confidence", "evidence_reference",
                  "next_command", "proposed_fix", "human_review", "reviewer_note"]

    out_path = os.path.join(DATA_DIR, "cases.csv")
    rows = []
    for cid, c in cases.items():
        a = ai.get(cid, {})
        r = review.get(cid, {})
        rows.append({
            "case_id": cid,
            "issue_type": c["concept_tag"],
            "symptom": c["symptom"],
            "topology_note": c["topology_note"],
            "show_outputs": c["show_output"],
            "expected_fault": c["expected_fault"],
            "osi_layer": c["osi_layer"],
            "concept_tag": c["concept_tag"],
            "severity": c["severity"],
            "ai_root_cause": a.get("root_cause", ""),
            "ai_confidence": a.get("confidence", ""),
            "evidence_reference": a.get("evidence", ""),
            "next_command": a.get("next_command", ""),
            "proposed_fix": a.get("fix_steps", ""),
            "human_review": r.get("status", ""),
            "reviewer_note": r.get("notes", ""),
        })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Rewrote {out_path} with {len(rows)} rows and {len(fieldnames)} columns.")


if __name__ == "__main__":
    main()
