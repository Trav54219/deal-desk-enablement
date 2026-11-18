"""Battlecard generator from a structured competitor YAML."""
import yaml

REQUIRED = ["name", "positioning", "strengths", "weaknesses", "objections"]


def load(path):
    with open(path) as f:
        doc = yaml.safe_load(f)
    for c in doc.get("competitors", []):
        missing = [k for k in REQUIRED if k not in c]
        if missing:
            raise ValueError(f"competitor {c.get('name', '?')} missing fields: {missing}")
    return doc


def _bullets(items):
    return "\n".join(f"- {i}" for i in items) or "- (none)"


def render_card(our_product, c):
    parts = [
        f"# Battlecard: {our_product} vs {c['name']}", "",
        f"**Positioning:** {c['positioning']}", "",
        "## Where they are strong", _bullets(c["strengths"]), "",
        "## Where they are weak", _bullets(c["weaknesses"]), "",
        "## Landmine questions", _bullets(c.get("landmines", [])), "",
        "## Objection handling",
    ]
    for o in c["objections"]:
        parts += [f"**\"{o['objection']}\"**", f"> {o['response']}", ""]
    parts += ["## Proof points to send", _bullets(c.get("proof_points", [])), "",
              "## Discount guidance", c.get("discount_guidance", "Follow the standard approval matrix."), ""]
    return "\n".join(parts)


def render_all(path):
    doc = load(path)
    return {c["name"]: render_card(doc["our_product"], c) for c in doc["competitors"]}
