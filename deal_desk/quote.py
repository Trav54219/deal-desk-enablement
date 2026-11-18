"""Quote builder: line items, discount, margin, approval decision."""
from dataclasses import dataclass, field
from . import approval

# Synthetic catalog: sku -> (name, list price per unit per year, unit cost fraction)
CATALOG = {
    "PLAT": ("Platform License", 1200.00, 0.28),
    "ANLY": ("Analytics Add-on", 400.00, 0.22),
    "SUPP": ("Premium Support", 250.00, 0.55),
    "ONBD": ("Onboarding Package", 5000.00, 0.65),
}


@dataclass
class Line:
    sku: str
    qty: int
    discount_pct: float = 0.0

    @property
    def name(self):
        return CATALOG[self.sku][0]

    @property
    def list_total(self):
        return round(CATALOG[self.sku][1] * self.qty, 2)

    @property
    def net_total(self):
        return round(self.list_total * (1 - self.discount_pct / 100), 2)

    @property
    def cost_total(self):
        return round(self.list_total * CATALOG[self.sku][2], 2)


@dataclass
class Quote:
    customer: str
    segment: str
    lines: list
    terms: dict = field(default_factory=dict)

    @property
    def list_total(self):
        return round(sum(l.list_total for l in self.lines), 2)

    @property
    def net_total(self):
        return round(sum(l.net_total for l in self.lines), 2)

    @property
    def cost_total(self):
        return round(sum(l.cost_total for l in self.lines), 2)

    @property
    def blended_discount_pct(self):
        if not self.list_total:
            return 0.0
        return round((1 - self.net_total / self.list_total) * 100, 2)

    @property
    def margin_pct(self):
        if not self.net_total:
            return 0.0
        return round((1 - self.cost_total / self.net_total) * 100, 2)

    def decision(self):
        return approval.evaluate(
            self.segment, self.blended_discount_pct, self.margin_pct, self.terms
        )


def build_quote(customer, segment, items, terms=None):
    """items: list of (sku, qty, discount_pct)."""
    if segment not in approval.MARGIN_FLOOR:
        raise ValueError(f"unknown segment {segment!r}")
    lines = []
    for sku, qty, disc in items:
        if sku not in CATALOG:
            raise ValueError(f"unknown sku {sku!r}")
        if qty <= 0:
            raise ValueError("qty must be positive")
        lines.append(Line(sku, qty, disc))
    return Quote(customer, segment, lines, terms or {})
