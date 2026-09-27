"""
NetSage AI - Dashboard builder
================================
Step 6 of the workflow: "Build the dashboard... Show counts by issue type
and a demo of one broken lab being diagnosed, reviewed, fixed, verified."

Produces dashboard/dashboard.xlsx with:
  - "Raw Data" sheet: one row per case joining cases.csv + agreement_report
    + human_review_log (the single source every summary formula reads from)
  - "Dashboard" sheet: COUNTIFS-driven summary tables (issue type, severity,
    review status, AI-vs-human agreement rate) + two charts

All dashboard numbers are formulas over "Raw Data", not hardcoded, so the
dashboard recalculates if cases are added or a review status changes.
"""
import csv
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.utils import get_column_letter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
LOG_DIR = os.path.join(BASE, "logs")
OUT_DIR = os.path.join(BASE, "dashboard")
os.makedirs(OUT_DIR, exist_ok=True)

FONT = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(name=FONT, bold=True, size=14, color="1F4E78")
LABEL_FONT = Font(name=FONT, bold=True, size=11)
BODY_FONT = Font(name=FONT, size=10)
THIN = Side(style="thin", color="B7C6DB")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    cases = {r["case_id"]: r for r in load_csv(os.path.join(DATA_DIR, "cases.csv"))}
    agreement = {r["case_id"]: r for r in load_csv(os.path.join(LOG_DIR, "agreement_report.csv"))}
    review = {r["case_id"]: r for r in load_csv(os.path.join(LOG_DIR, "human_review_log.csv"))}

    wb = Workbook()

    # ---------------- Raw Data sheet ----------------
    ws = wb.active
    ws.title = "Raw Data"
    headers = ["case_id", "concept_tag", "severity", "osi_layer", "ai_confidence",
               "agrees_with_expected", "review_status"]
    ws.append(headers)
    for cid, c in cases.items():
        a = agreement.get(cid, {})
        r = review.get(cid, {})
        ws.append([
            cid, c["concept_tag"], c["severity"], c["osi_layer"],
            a.get("ai_confidence", ""), a.get("agrees_with_expected", ""),
            r.get("status", ""),
        ])
    n_rows = ws.max_row  # includes header

    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")
    for row in ws.iter_rows(min_row=2, max_row=n_rows, max_col=len(headers)):
        for cell in row:
            cell.font = BODY_FONT
            cell.border = BORDER
    for col, w in zip("ABCDEFG", [10, 14, 10, 14, 14, 20, 16]):
        ws.column_dimensions[col].width = w

    data_range_last_row = n_rows  # e.g. 37 for 36 cases + header

    # ---------------- Dashboard sheet ----------------
    dash = wb.create_sheet("Dashboard")
    dash["B2"] = "NetSage AI — Case Dashboard"
    dash["B2"].font = TITLE_FONT
    dash["B3"] = "All figures below are live formulas over the 'Raw Data' sheet."
    dash["B3"].font = Font(name=FONT, italic=True, size=9, color="666666")

    # --- Table 1: Issue type counts ---
    dash["B5"] = "Issue Type"
    dash["C5"] = "Case Count"
    dash["B5"].font = HEADER_FONT; dash["B5"].fill = HEADER_FILL
    dash["C5"].font = HEADER_FONT; dash["C5"].fill = HEADER_FILL
    concept_tags = ["VLAN", "Gateway", "DHCP", "DNS", "Routing", "ACL", "NAT", "Wireless"]
    for i, tag in enumerate(concept_tags):
        r = 6 + i
        dash.cell(row=r, column=2, value=tag).font = BODY_FONT
        dash.cell(row=r, column=3,
                  value=f"=COUNTIF('Raw Data'!B2:B{data_range_last_row},B{r})").font = BODY_FONT
    total_row = 6 + len(concept_tags)
    dash.cell(row=total_row, column=2, value="Total").font = LABEL_FONT
    dash.cell(row=total_row, column=3,
              value=f"=SUM(C6:C{total_row-1})").font = LABEL_FONT
    for r in range(5, total_row + 1):
        for c in (2, 3):
            dash.cell(row=r, column=c).border = BORDER

    # --- Table 2: Severity breakdown ---
    dash["E5"] = "Severity"
    dash["F5"] = "Case Count"
    dash["E5"].font = HEADER_FONT; dash["E5"].fill = HEADER_FILL
    dash["F5"].font = HEADER_FONT; dash["F5"].fill = HEADER_FILL
    severities = ["High", "Medium", "Low"]
    for i, sev in enumerate(severities):
        r = 6 + i
        dash.cell(row=r, column=5, value=sev).font = BODY_FONT
        dash.cell(row=r, column=6,
                  value=f"=COUNTIF('Raw Data'!C2:C{data_range_last_row},E{r})").font = BODY_FONT
    sev_total_row = 6 + len(severities)
    dash.cell(row=sev_total_row, column=5, value="Total").font = LABEL_FONT
    dash.cell(row=sev_total_row, column=6, value=f"=SUM(F6:F{sev_total_row-1})").font = LABEL_FONT
    for r in range(5, sev_total_row + 1):
        for c in (5, 6):
            dash.cell(row=r, column=c).border = BORDER

    # --- Table 3: Human review status ---
    review_start = total_row + 3
    dash.cell(row=review_start, column=2, value="Review Status").font = HEADER_FONT
    dash.cell(row=review_start, column=2).fill = HEADER_FILL
    dash.cell(row=review_start, column=3, value="Case Count").font = HEADER_FONT
    dash.cell(row=review_start, column=3).fill = HEADER_FILL
    statuses = ["Accepted", "Edited", "Rejected"]
    for i, st in enumerate(statuses):
        r = review_start + 1 + i
        dash.cell(row=r, column=2, value=st).font = BODY_FONT
        dash.cell(row=r, column=3,
                  value=f"=COUNTIF('Raw Data'!G2:G{data_range_last_row},B{r})").font = BODY_FONT
    review_total_row = review_start + 1 + len(statuses)
    dash.cell(row=review_total_row, column=2, value="Total").font = LABEL_FONT
    dash.cell(row=review_total_row, column=3,
              value=f"=SUM(C{review_start+1}:C{review_total_row-1})").font = LABEL_FONT
    for r in range(review_start, review_total_row + 1):
        for c in (2, 3):
            dash.cell(row=r, column=c).border = BORDER

    # --- Table 4: AI vs human agreement rate ---
    agree_row_label = review_total_row + 2
    dash.cell(row=agree_row_label, column=2, value="AI vs. Known-Correct Agreement").font = LABEL_FONT
    dash.cell(row=agree_row_label + 1, column=2, value="Cases where AI matched expected fault").font = BODY_FONT
    dash.cell(row=agree_row_label + 1, column=3,
              value=f"=COUNTIF('Raw Data'!F2:F{data_range_last_row},\"Yes\")").font = BODY_FONT
    dash.cell(row=agree_row_label + 2, column=2, value="Total cases").font = BODY_FONT
    dash.cell(row=agree_row_label + 2, column=3,
              value=f"=COUNTA('Raw Data'!A2:A{data_range_last_row})").font = BODY_FONT
    dash.cell(row=agree_row_label + 3, column=2, value="Agreement rate").font = LABEL_FONT
    dash.cell(row=agree_row_label + 3, column=3,
              value=f"=C{agree_row_label+1}/C{agree_row_label+2}").font = LABEL_FONT
    dash.cell(row=agree_row_label + 3, column=3).number_format = "0.0%"

    dash.cell(row=agree_row_label + 5, column=2,
              value="Human-corrected cases (Edited + Rejected)").font = BODY_FONT
    dash.cell(row=agree_row_label + 5, column=3,
              value=f"=C{review_start+2}+C{review_start+3}").font = BODY_FONT

    for r in range(agree_row_label, agree_row_label + 6):
        for c in (2, 3):
            dash.cell(row=r, column=c).border = BORDER

    dash.column_dimensions["A"].width = 2
    dash.column_dimensions["B"].width = 32
    dash.column_dimensions["C"].width = 12
    dash.column_dimensions["D"].width = 3
    dash.column_dimensions["E"].width = 14
    dash.column_dimensions["F"].width = 12

    # --- Charts ---
    bar = BarChart()
    bar.title = "Cases by Issue Type"
    bar.y_axis.title = "Case count"
    bar.x_axis.title = "Issue type"
    data_ref = Reference(dash, min_col=3, min_row=5, max_row=total_row - 1)
    cats_ref = Reference(dash, min_col=2, min_row=6, max_row=total_row - 1)
    bar.add_data(data_ref, titles_from_data=True)
    bar.set_categories(cats_ref)
    bar.height, bar.width = 8, 14
    dash.add_chart(bar, "H5")

    pie = PieChart()
    pie.title = "Human Review Outcomes"
    pdata = Reference(dash, min_col=3, min_row=review_start, max_row=review_total_row - 1)
    pcats = Reference(dash, min_col=2, min_row=review_start + 1, max_row=review_total_row - 1)
    pie.add_data(pdata, titles_from_data=True)
    pie.set_categories(pcats)
    pie.height, pie.width = 8, 14
    dash.add_chart(pie, "H22")

    out_path = os.path.join(OUT_DIR, "dashboard.xlsx")
    wb.save(out_path)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
