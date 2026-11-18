from datetime import date, timedelta
import pytest

from deal_desk import approval, battlecard, content, data, pricing, proposal, quote, ramp, cli
from pathlib import Path

YAML = Path(__file__).resolve().parent.parent / "data" / "competitors.yaml"


# approval matrix
@pytest.mark.parametrize("disc,level", [(0, "rep"), (10, "rep"), (10.1, "manager"), (20, "manager"),
                                         (25, "finance"), (30, "finance"), (31, "cro"), (45, "cro")])
def test_discount_levels(disc, level):
    assert approval.evaluate("SMB", disc, 80).required_level == level


def test_hard_stop_rejects():
    assert approval.evaluate("SMB", 46, 80).status == "rejected"


def test_margin_floor_escalates_to_finance():
    d = approval.evaluate("Enterprise", 5, 40)
    assert d.required_level == "finance" and d.status == "needs_approval"


def test_margin_at_floor_ok():
    assert approval.evaluate("Enterprise", 5, 50).status == "approved"


def test_term_flags():
    t = {"payment_days": 90, "auto_renew": False, "most_favored_customer": True}
    d = approval.evaluate("SMB", 0, 90, t)
    assert set(d.flags) == {"extended_payment_terms", "no_auto_renew", "most_favored_customer"}
    assert d.required_level == "cro"


def test_standard_terms_no_flags():
    assert approval.term_flags({"payment_days": 30}) == []


# quote
def test_quote_math():
    q = quote.build_quote("X", "SMB", [("PLAT", 10, 10)])
    assert q.list_total == 12000.0 and q.net_total == 10800.0
    assert q.blended_discount_pct == 10.0
    assert q.margin_pct == round((1 - 3360 / 10800) * 100, 2)


def test_quote_rejects_bad_input():
    with pytest.raises(ValueError):
        quote.build_quote("X", "SMB", [("NOPE", 1, 0)])
    with pytest.raises(ValueError):
        quote.build_quote("X", "Nope", [("PLAT", 1, 0)])
    with pytest.raises(ValueError):
        quote.build_quote("X", "SMB", [("PLAT", 0, 0)])


# pricing
def test_bands_and_realization():
    deals = [
        {"segment": "SMB", "list_price": 100, "discount_pct": 4, "net_price": 96, "won": True},
        {"segment": "SMB", "list_price": 100, "discount_pct": 12, "net_price": 88, "won": False},
        {"segment": "SMB", "list_price": 100, "discount_pct": 12, "net_price": 88, "won": True},
    ]
    wr = pricing.win_rate_by_band(deals)
    assert wr["0-5%"]["win_rate"] == 100.0 and wr["10-20%"]["win_rate"] == 50.0
    assert wr["30%+"]["win_rate"] is None
    assert pricing.price_realization(deals)["ALL"] == 92.0
    assert pricing.discount_distribution(deals)["SMB"]["median"] == 12


def test_band_edges():
    assert pricing.band_for(5) == "5-10%" and pricing.band_for(30) == "30%+"


# data determinism
def test_data_seeded():
    assert data.make_deals(50)[:3] == data.make_deals(50)[:3]
    assert len(data.make_deals(50)) == 50


# proposal
def test_proposal_md_and_html():
    q = quote.build_quote("Acme <b>", "SMB", [("PLAT", 5, 0)], {"payment_days": 30})
    md = proposal.generate(q, "2026-12-31", "OF-1", "md")
    assert "Acme <b>" in md and "$6,000.00" in md and "{{" not in md
    h = proposal.generate(q, "2026-12-31", "OF-1", "html")
    assert "Acme &lt;b&gt;" in h and "{{" not in h


def test_proposal_missing_field():
    with pytest.raises(KeyError):
        proposal.render("order_form.md", {})


# battlecard
def test_battlecards():
    cards = battlecard.render_all(YAML)
    assert len(cards) == 2 and "Landmine questions" in cards["Contoso Suite"]


def test_battlecard_validation(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("our_product: X\ncompetitors:\n  - name: A\n")
    with pytest.raises(ValueError):
        battlecard.load(p)


# ramp
def test_ramp_status_and_ttfd():
    rep = {"rep_id": "R1", "start_date": date(2026, 1, 1)}
    ev = {"product_certified": date(2026, 1, 10), "first_deal_closed": date(2026, 4, 1)}
    st = ramp.rep_status(rep, ev, date(2026, 6, 1))
    assert st["product_certified"]["status"] == "done" and not st["product_certified"]["late"]
    assert st["first_demo_delivered"]["status"] == "overdue"
    assert ramp.time_to_first_deal(rep, ev) == 90
    assert ramp.rep_status(rep, {}, date(2026, 1, 5))["product_certified"]["status"] == "pending"


# content
def test_content_lift():
    deals = ([{"won": True, "content": ["a"]}] * 3 + [{"won": False, "content": ["a"]}]
             + [{"won": True, "content": []}] + [{"won": False, "content": []}] * 3)
    rows, overall = content.usage_report(deals, min_n=2)
    assert rows[0]["asset"] == "a" and rows[0]["lift_pp"] == 50.0 and overall == 50.0
    assert not rows[0]["low_sample"]


# end to end
def test_cli_writes_reports(tmp_path):
    cli.main(["--out", str(tmp_path)])
    names = {p.name for p in tmp_path.iterdir()}
    assert {"order_form.md", "order_form.html", "pricing_analysis.md", "content_report.md",
            "ramp_tracker.md"} <= names
