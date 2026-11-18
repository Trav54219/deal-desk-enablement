"""Seeded synthetic data generators. Nothing here is real."""
import random
from datetime import date, timedelta

SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
LIST_RANGE = {"SMB": (8_000, 30_000), "Mid-Market": (30_000, 120_000), "Enterprise": (120_000, 500_000)}
# Generator assumptions (documented, not findings): bigger discounts lift
# close odds slightly but with diminishing returns.
BASE_WIN = {"SMB": 0.34, "Mid-Market": 0.28, "Enterprise": 0.22}
CONTENT = {
    "case-study-fintech": 0.06, "roi-calculator": 0.05, "security-whitepaper": 0.03,
    "competitor-battlecard": 0.04, "exec-deck": 0.0, "product-datasheet": -0.01,
    "pricing-faq": 0.0, "demo-recording": 0.02,
}


def make_reps(n=16, seed=7):
    rng = random.Random(seed)
    reps = []
    for i in range(n):
        start = date(2025, 1, 6) + timedelta(days=rng.randint(0, 540))
        reps.append({"rep_id": f"R{i+1:02d}", "name": f"Rep {i+1:02d}", "start_date": start})
    return reps


def make_deals(n=600, seed=11):
    rng = random.Random(seed)
    reps = make_reps(seed=seed - 4)
    deals = []
    for i in range(n):
        seg = rng.choices(SEGMENTS, weights=[5, 3, 2])[0]
        lo, hi = LIST_RANGE[seg]
        list_price = round(rng.uniform(lo, hi), -2)
        disc = max(0.0, min(45.0, rng.gauss({"SMB": 9, "Mid-Market": 15, "Enterprise": 22}[seg], 7)))
        disc = round(disc, 1)
        used = [c for c in CONTENT if rng.random() < 0.35]
        p = BASE_WIN[seg] + min(disc, 25) * 0.004 + sum(CONTENT[c] for c in used)
        won = rng.random() < max(0.02, min(0.95, p))
        rep = rng.choice(reps)
        close = date(2026, 1, 1) + timedelta(days=rng.randint(0, 300))
        deals.append({
            "deal_id": f"D{i+1:04d}", "rep_id": rep["rep_id"], "segment": seg,
            "list_price": list_price, "discount_pct": disc,
            "net_price": round(list_price * (1 - disc / 100), 2),
            "won": won, "close_date": close, "content": used,
        })
    return deals
