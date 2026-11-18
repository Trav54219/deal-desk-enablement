"""Proposal / order form generator from markdown or HTML templates."""
import html
import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
_TAG = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def _money(x):
    return f"${x:,.2f}"


def context_from_quote(quote, valid_until, order_ref):
    d = quote.decision()
    rows_md = "\n".join(
        f"| {l.name} | {l.qty} | {_money(l.list_total)} | {l.discount_pct:.1f}% | {_money(l.net_total)} |"
        for l in quote.lines
    )
    t = quote.terms
    return {
        "customer": quote.customer, "order_ref": order_ref, "valid_until": valid_until,
        "line_rows": rows_md,
        "list_total": _money(quote.list_total), "net_total": _money(quote.net_total),
        "discount_pct": f"{quote.blended_discount_pct:.1f}",
        "payment_days": str(t.get("payment_days", 30)),
        "auto_renew": "Yes" if t.get("auto_renew", True) else "No",
        "approval_status": f"{d.status} ({d.required_level})",
    }


def render(template_name, ctx, html_mode=None):
    text = (TEMPLATES / template_name).read_text()
    if html_mode is None:
        html_mode = template_name.endswith(".html")

    def sub(m):
        key = m.group(1)
        if key not in ctx:
            raise KeyError(f"template field {key!r} missing from context")
        val = str(ctx[key])
        if html_mode and key != "line_rows":
            val = html.escape(val)
        return val

    return _TAG.sub(sub, text)


def html_rows(quote):
    out = []
    for l in quote.lines:
        cells = [l.name, str(l.qty), _money(l.list_total), f"{l.discount_pct:.1f}%", _money(l.net_total)]
        out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>")
    return "\n".join(out)


def generate(quote, valid_until, order_ref, fmt="md"):
    ctx = context_from_quote(quote, valid_until, order_ref)
    if fmt == "html":
        ctx["line_rows"] = html_rows(quote)
        return render("order_form.html", ctx)
    return render("order_form.md", ctx)
