"""Rep onboarding / ramp tracker."""
from datetime import date

# milestone -> target days from start date
MILESTONES = {
    "product_certified": 14,
    "first_demo_delivered": 30,
    "first_qualified_opp": 45,
    "first_deal_closed": 90,
}


def days_between(a, b):
    return (b - a).days


def rep_status(rep, events, today):
    """events: {milestone: date}. Returns per-milestone status and overall."""
    start = rep["start_date"]
    rows = {}
    for m, target in MILESTONES.items():
        done = events.get(m)
        if done:
            took = days_between(start, done)
            rows[m] = {"status": "done", "days": took, "target": target, "late": took > target}
        else:
            age = days_between(start, today)
            rows[m] = {"status": "overdue" if age > target else "pending",
                       "days": None, "target": target, "late": age > target}
    return rows


def time_to_first_deal(rep, events):
    d = events.get("first_deal_closed")
    return days_between(rep["start_date"], d) if d else None


def summarize(reps, all_events, today):
    out = []
    for r in reps:
        ev = all_events.get(r["rep_id"], {})
        st = rep_status(r, ev, today)
        out.append({
            "rep_id": r["rep_id"], "start": r["start_date"],
            "ttfd": time_to_first_deal(r, ev),
            "overdue": [m for m, v in st.items() if v["status"] == "overdue"],
            "done": sum(1 for v in st.values() if v["status"] == "done"),
        })
    ttfds = sorted(o["ttfd"] for o in out if o["ttfd"] is not None)
    median = ttfds[len(ttfds) // 2] if ttfds else None
    return out, median


def synth_events(reps, seed=3):
    """Synthetic milestone completions; some reps still ramping."""
    import random
    from datetime import timedelta
    rng = random.Random(seed)
    events = {}
    for r in reps:
        ev, offset = {}, 0
        for m, target in MILESTONES.items():
            offset += max(1, int(rng.gauss(target * 0.55, target * 0.2)))
            if rng.random() < 0.9:
                ev[m] = r["start_date"] + timedelta(days=min(offset, int(target * 1.8)))
            else:
                break
        events[r["rep_id"]] = ev
    return events


def render_markdown(reps, all_events, today):
    rows, median = summarize(reps, all_events, today)
    lines = ["# Rep ramp tracker (synthetic data)", "", f"As of {today}. Targets: " +
             ", ".join(f"{m}={t}d" for m, t in MILESTONES.items()), "",
             "| Rep | Start | Milestones done | Time to first deal (days) | Overdue |", "|---|---|---|---|---|"]
    for o in rows:
        lines.append(f"| {o['rep_id']} | {o['start']} | {o['done']}/{len(MILESTONES)} | "
                     f"{o['ttfd'] if o['ttfd'] is not None else '-'} | {', '.join(o['overdue']) or '-'} |")
    lines += ["", f"Median time to first deal (reps with a deal): {median if median is not None else 'n/a'}"]
    return "\n".join(lines) + "\n"
