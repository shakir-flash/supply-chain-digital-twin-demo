# nlp/router.py
import re
from typing import Optional, Tuple, Dict, Any

# Intent schema:
# {"name": "<intent>", "args": {...}}

_PATTERNS: list[Tuple[re.Pattern, str, Dict[str, Any]]] = [
    # totals / headline KPIs
    (re.compile(r"\b(total )?cost\b.*(penalty|with penalty)?", re.I), "total_cost", {}),
    (re.compile(r"\btransport(ation)? cost\b", re.I), "transport_cost", {}),
    (re.compile(r"\bunmet\b.*(units|demand)", re.I), "unmet_units", {}),
    (re.compile(r"\bslow lanes?\b.*(top\s*(\d+))?", re.I), "slow_lanes", {"top": 5}),
    # utilization
    (re.compile(r"\bhighest\b.*utili[sz]ation\b", re.I), "highest_util_dc", {}),
    (re.compile(r"\blowest\b.*utili[sz]ation\b", re.I), "lowest_util_dc", {}),
    (re.compile(r"\b(utili[sz]ation|util)\b.*\b(?P<dc>[A-Z0-9_]+)", re.I), "dc_util", {}),
    # cost by region / dc
    (re.compile(r"\bcost by region\b.*(top\s*(\d+))?", re.I), "cost_by_region", {"order": "desc", "top": 3}),
    (re.compile(r"\bwhich region\b.*cost\b(high|most)", re.I), "cost_by_region", {"order": "desc", "top": 1}),
    (re.compile(r"\bwhich region\b.*cost\b(low|least)", re.I), "cost_by_region", {"order": "asc", "top": 1}),
    (re.compile(r"\bcost by dc\b.*(top\s*(\d+))?", re.I), "cost_by_dc", {"order": "desc", "top": 5}),
    # coverage
    (re.compile(r"\bstores served by\b\s*(?P<dc>[A-Z0-9_]+)", re.I), "stores_served_by_dc", {}),
    (re.compile(r"\blist stores\b.*\b(?P<dc>[A-Z0-9_]+)", re.I), "stores_for_dc", {"top": 20}),
    # flows / service
    (re.compile(r"\btop\b\s*(?P<n>\d+)\s*slow lanes", re.I), "slow_lanes", {}),
]

def route(question: str) -> Optional[Dict[str, Any]]:
    q = question.strip()
    for pat, intent, defaults in _PATTERNS:
        m = pat.search(q)
        if not m:
            continue
        args = dict(defaults)
        # extract group numbers if present
        if intent in ("slow_lanes", "cost_by_region", "cost_by_dc"):
            # top N
            n_match = re.search(r"top\s*(\d+)", q, re.I)
            if n_match:
                args["top"] = int(n_match.group(1))
        # order asc/desc hints
        if intent in ("cost_by_region", "cost_by_dc"):
            if re.search(r"\blow|least|bottom\b", q, re.I):
                args["order"] = "asc"
            elif re.search(r"\bhigh|most|top\b", q, re.I):
                args["order"] = "desc"
        # dc capture
        if "dc" in m.groupdict() and m.group("dc"):
            args["dc_id"] = m.group("dc").upper()
        # explicit n
        if "n" in m.groupdict() and m.group("n"):
            args["top"] = int(m.group("n"))
        return {"name": intent, "args": args}
    return None
