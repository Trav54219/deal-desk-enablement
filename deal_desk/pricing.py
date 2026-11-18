"""Pricing analysis over closed deals."""
import statistics

BANDS = [(0, 5, "0-5%"), (5, 10, "5-10%"), (10, 20, "10-20%"), (20, 30, "20-30%"), (30, 1000, "30%+")]


def band_for(disc):
    for lo, hi, label in BANDS:
        if lo <= disc < hi:
            return label
    return BANDS[-1][2]


def _pct(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(round(q * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


def discount_distribution(deals):
    """Per segment: count, mean, median, p90 discount (won and lost, all quotes)."""
    out = {}
    for seg in sorted({d["segment"] for d in deals}):
        vals = sorted(d["discount_pct"] for d in deals if d["segment"] == seg)
        out[seg] = {
            "n": len(vals), "mean": round(statistics.mean(vals), 2),
            "median": round(statistics.median(vals), 2), "p90": round(_pct(vals, 0.9), 2),
        }
    return out


def price_realization(deals):
    """Net / list on won deals, dollar weighted, per segment and overall."""
    out = {}
    groups = {"ALL": [d for d in deals if d["won"]]}
    for seg in sorted({d["segment"] for d in deals}):
        groups[seg] = [d for d in deals if d["won"] and d["segment"] == seg]
    for k, ds in groups.items():
        lp = sum(d["list_price"] for d in ds)
        out[k] = round(sum(d["net_price"] for d in ds) / lp * 100, 2) if lp else None
    return out


def win_rate_by_band(deals, min_n=10):
    rows = {}
    for _, _, label in BANDS:
        ds = [d for d in deals if band_for(d["discount_pct"]) == label]
        n = len(ds)
        wins = sum(d["won"] for d in ds)
        rows[label] = {
            "n": n, "wins": wins,
            "win_rate": round(wins / n * 100, 1) if n else None,
            "low_sample": n < min_n,
        }
    return rows


def render_markdown(deals):
    lines = ["# Pricing analysis (synthetic data)", "", "## Discount distribution by segment", "",
             "| Segment | Quotes | Mean % | Median % | P90 % |", "|---|---|---|---|---|"]
    for s, v in discount_distribution(deals).items():
        lines.append(f"| {s} | {v['n']} | {v['mean']} | {v['median']} | {v['p90']} |")
    lines += ["", "## Price realization (won deals, net/list)", ""]
    for k, v in price_realization(deals).items():
        lines.append(f"- {k}: {v}%")
    lines += ["", "## Win rate by discount band", "", "| Band | Quotes | Wins | Win rate % | Note |", "|---|---|---|---|---|"]
    for b, v in win_rate_by_band(deals).items():
        note = "low sample" if v["low_sample"] else ""
        lines.append(f"| {b} | {v['n']} | {v['wins']} | {v['win_rate']} | {note} |")
    return "\n".join(lines) + "\n"
