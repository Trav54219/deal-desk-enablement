"""Content usage and win correlation report.

Correlation only: deals that used an asset differ from those that did not in
ways this data cannot control for (segment, rep, stage). Treat as a lead for
investigation, not proof the asset causes wins.
"""


def usage_report(deals, min_n=15):
    assets = sorted({c for d in deals for c in d["content"]})
    total_wr = sum(d["won"] for d in deals) / len(deals) * 100 if deals else 0
    rows = []
    for a in assets:
        used = [d for d in deals if a in d["content"]]
        unused = [d for d in deals if a not in d["content"]]
        wr_u = sum(d["won"] for d in used) / len(used) * 100 if used else None
        wr_n = sum(d["won"] for d in unused) / len(unused) * 100 if unused else None
        lift = round(wr_u - wr_n, 1) if wr_u is not None and wr_n is not None else None
        rows.append({
            "asset": a, "deals_used": len(used), "win_rate_used": round(wr_u, 1) if wr_u is not None else None,
            "win_rate_not_used": round(wr_n, 1) if wr_n is not None else None,
            "lift_pp": lift, "low_sample": len(used) < min_n,
        })
    rows.sort(key=lambda r: (r["lift_pp"] is None, -(r["lift_pp"] or 0)))
    return rows, round(total_wr, 1)


def render_markdown(deals):
    rows, overall = usage_report(deals)
    lines = ["# Content usage and win correlation (synthetic data)", "",
             f"Overall win rate: {overall}%. Lift is percentage points, used vs not used. "
             "Correlation only, not causation.", "",
             "| Asset | Deals used | Win % used | Win % not used | Lift (pp) | Note |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['asset']} | {r['deals_used']} | {r['win_rate_used']} | "
                     f"{r['win_rate_not_used']} | {r['lift_pp']} | {'low sample' if r['low_sample'] else ''} |")
    return "\n".join(lines) + "\n"
