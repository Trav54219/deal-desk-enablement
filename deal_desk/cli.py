"""Command line entry: `dealdesk all --out out/` writes every report."""
import argparse
from datetime import date
from pathlib import Path

from . import battlecard, content, data, pricing, proposal, quote, ramp

ROOT = Path(__file__).resolve().parent.parent


def demo_quote():
    return quote.build_quote(
        "Example Corp (fictional)", "Mid-Market",
        [("PLAT", 50, 18), ("ANLY", 50, 12), ("SUPP", 50, 5)],
        {"payment_days": 60, "auto_renew": True},
    )


def main(argv=None):
    p = argparse.ArgumentParser(prog="dealdesk")
    p.add_argument("--out", default="out")
    p.add_argument("--today", default="2026-11-18")
    a = p.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    deals = data.make_deals()
    reps = data.make_reps(seed=7)
    today = date.fromisoformat(a.today)

    q = demo_quote()
    (out / "order_form.md").write_text(proposal.generate(q, "2026-12-31", "OF-0001", "md"))
    (out / "order_form.html").write_text(proposal.generate(q, "2026-12-31", "OF-0001", "html"))
    (out / "pricing_analysis.md").write_text(pricing.render_markdown(deals))
    (out / "content_report.md").write_text(content.render_markdown(deals))
    (out / "ramp_tracker.md").write_text(ramp.render_markdown(reps, ramp.synth_events(reps), today))
    for name, card in battlecard.render_all(ROOT / "data" / "competitors.yaml").items():
        (out / f"battlecard_{name.lower().replace(' ', '_')}.md").write_text(card)
    d = q.decision()
    print(f"demo quote: discount {q.blended_discount_pct}% margin {q.margin_pct}% -> {d.status} ({d.required_level})")
    print(f"wrote reports to {out}/")


if __name__ == "__main__":
    main()
