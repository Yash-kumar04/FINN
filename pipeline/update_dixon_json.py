import json

path = "web/public/data/research/DIXON.json"
d = json.load(open(path, encoding="utf-8"))

d["jul_2026_revenue_check"] = {
    "source_label": "NSE results filing",
    "line_label": "Revenue from operations",
    "q2_fy27_revenue_cr": 21793.64,
    "q1_fy27_revenue_cr": 15547.66,
    "qoq_growth_pct": 40.2,
    "formula": "(21793.64 - 15547.66) / 15547.66 = +40.173% (~ +40.2%)",
    "verdict": "Unclear (Revenue growth is not volume growth)"
}

for r in d.get("promised_vs_delivered", []):
    if r.get("period") == "Q2 FY27" and r.get("metric") == "volume":
        r["delivered"] = "+40.2% QoQ revenue growth (Q2 FY27 ₹21,793.64 Cr vs Q1 FY27 ₹15,547.66 Cr from 'Revenue from operations')"
        r["delivered_figure"] = r["delivered"]
        r["delivered_source"] = "NSE results filing (results.json, p.11)"
        r["verdict"] = "Unclear"
        r["outcome"] = "Delivered metric is revenue (+40.2%), not volume"
    if r.get("fact_id") == "fact_guidance_13":
        r["statement"] = "Q2 FY27 (p.4): Promised '20% to 25% volume growth QoQ in Q2 FY27', Delivered '+40.2% QoQ revenue growth (Q2 FY27 ₹21,793.64 Cr vs Q1 FY27 ₹15,547.66 Cr from 'Revenue from operations')', Verdict: Unclear. (Delivered metric is revenue (+40.2%), not volume)"

with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print("Updated DIXON.json successfully!")

