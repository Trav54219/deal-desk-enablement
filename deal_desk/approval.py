"""Discount approval matrix, margin floors and non-standard term flags."""
from dataclasses import dataclass, field

# Ordered approver ladder. Each level can approve up to its discount ceiling.
LEVELS = ["rep", "manager", "finance", "cro"]
DISCOUNT_CEILING = {"rep": 10.0, "manager": 20.0, "finance": 30.0, "cro": 45.0}
HARD_STOP_DISCOUNT = 45.0  # above this the deal is rejected, not escalated

# Minimum gross margin % by segment. Below the floor needs finance at minimum.
MARGIN_FLOOR = {"SMB": 60.0, "Mid-Market": 55.0, "Enterprise": 50.0}

STANDARD_PAYMENT_DAYS = 45
MAX_STANDARD_TERM_MONTHS = 36

# flag -> minimum approver level
TERM_FLAG_LEVEL = {
    "extended_payment_terms": "finance",
    "no_auto_renew": "manager",
    "custom_sla": "manager",
    "most_favored_customer": "cro",
    "termination_for_convenience": "finance",
    "long_price_lock": "finance",
}


@dataclass
class Decision:
    status: str  # approved | needs_approval | rejected
    required_level: str
    reasons: list = field(default_factory=list)
    flags: list = field(default_factory=list)


def _rank(level):
    return LEVELS.index(level)


def _max_level(a, b):
    return a if _rank(a) >= _rank(b) else b


def level_for_discount(discount_pct):
    for lvl in LEVELS:
        if discount_pct <= DISCOUNT_CEILING[lvl]:
            return lvl
    return None


def term_flags(terms):
    """Return list of non-standard term flags from a terms dict."""
    flags = []
    if terms.get("payment_days", 30) > STANDARD_PAYMENT_DAYS:
        flags.append("extended_payment_terms")
    if terms.get("auto_renew", True) is False:
        flags.append("no_auto_renew")
    if terms.get("custom_sla", False):
        flags.append("custom_sla")
    if terms.get("most_favored_customer", False):
        flags.append("most_favored_customer")
    if terms.get("termination_for_convenience", False):
        flags.append("termination_for_convenience")
    if terms.get("price_lock_months", 0) > MAX_STANDARD_TERM_MONTHS:
        flags.append("long_price_lock")
    return flags


def evaluate(segment, discount_pct, margin_pct, terms=None):
    terms = terms or {}
    reasons = []
    if discount_pct < 0:
        return Decision("rejected", "cro", ["negative discount"])
    if discount_pct > HARD_STOP_DISCOUNT:
        return Decision(
            "rejected", "cro",
            [f"discount {discount_pct:.1f}% exceeds hard stop {HARD_STOP_DISCOUNT:.0f}%"],
        )
    level = level_for_discount(discount_pct)
    reasons.append(f"discount {discount_pct:.1f}% needs {level}")

    floor = MARGIN_FLOOR[segment]
    if margin_pct < floor:
        level = _max_level(level, "finance")
        reasons.append(f"margin {margin_pct:.1f}% below {segment} floor {floor:.0f}%")

    flags = term_flags(terms)
    for f in flags:
        need = TERM_FLAG_LEVEL[f]
        level = _max_level(level, need)
        reasons.append(f"non-standard term '{f}' needs {need}")

    status = "approved" if level == "rep" else "needs_approval"
    return Decision(status, level, reasons, flags)
