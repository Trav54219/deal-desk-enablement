# deal-desk-enablement

A small Python toolkit covering deal desk, pricing analysis and sales enablement.

**All data is synthetic.** Deals, reps, discounts, content usage and competitors are generated from a seeded random generator or written by hand as fictional examples. **Nothing is connected to Salesforce CPQ, DealHub, Highspot or any other system.** Any pattern in the output (for example discount vs win rate, or content lift) comes from assumptions coded in `deal_desk/data.py`, not from real buyers. Do not read the output as findings about any market.

## What is in it

| Module | What it does |
|---|---|
| `approval.py`, `quote.py` | Quote builder with line items, blended discount, gross margin, and an approval matrix: rep / manager / finance / CRO discount ceilings, hard stop, per-segment margin floors, non-standard term flags (extended payment, no auto-renew, custom SLA, MFN, termination for convenience, long price lock) |
| `pricing.py` | Discount distribution by segment, price realization (net/list on won deals), win rate by discount band with low-sample flags |
| `proposal.py` | Order form generator from `templates/` (markdown and HTML, strict fields, HTML escaping) |
| `battlecard.py` | Battlecards from `data/competitors.yaml` (validated, fictional competitors) |
| `ramp.py` | Rep ramp tracker: milestones vs target days, overdue flags, time to first deal |
| `content.py` | Content usage and win-rate lift per asset (correlation only, low-sample flags) |

Approval thresholds and margin floors are constants at the top of `approval.py`; change them to model a different policy.

## Run

```bash
pip install -e ".[dev]"
python -m pytest
python -m deal_desk.cli --out out   # writes reports to ./out (git-ignored)
```

## Limits

- Win rate and content lift are not causal; no controls for segment, rep or stage.
- Floats are rounded to cents; a production system would use decimals and a real price book.
- The approval matrix is an illustrative policy, not advice.
