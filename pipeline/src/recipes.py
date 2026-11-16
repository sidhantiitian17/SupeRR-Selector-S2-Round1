"""Human-readable formulas for hybrid candidate names (used by the report, deck, guide and dashboard)."""
def describe(name, role):
    """Plain-text formula for a candidate name, e.g. 'H wB=0.5 +U+C | poolA'."""
    import re
    b_lab = "B strike-rate ensemble" if role == "bat" else "B economy + WPA"
    wb = float(re.search(r"wB=([0-9.]+)", name).group(1))
    wa = 1 - wb
    if name.startswith("HA(composite)"):
        return f"{wa:.2f} x z(A composite) + {wb:.2f} x z({b_lab})"
    core = f"{wa:.2f} x z(A rating) + {wb:.2f} x z({b_lab})"
    if "+U+C" in name:
        return f"0.8 x z[{core}] + 0.1 x z(uplift) + 0.1 x z(match consistency)"
    m = re.search(r"\+U([0-9.]+)", name)
    gate = " + 100 x [delivered under pressure]" if "gated" in name else ""
    if m:
        wu = float(m.group(1))
        return f"{1 - wu:.2f} x z[{core}] + {wu:.2f} x z(uplift){gate}"
    return f"{core}{gate}"


def components(name):
    """Which optional parts a candidate uses."""
    return {"composite": name.startswith("HA(composite)"), "uplift": "+U" in name,
            "consistency": "+U+C" in name or name.startswith("HA(composite)"), "gate": "gated" in name}
