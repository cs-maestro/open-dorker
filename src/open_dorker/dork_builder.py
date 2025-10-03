from itertools import product
from typing import Dict, List

def normalize_param(p: str) -> str:
    """Ensure params like 'site' -> 'site:' while letting raw 'site:' pass as-is."""
    p = p.strip()
    if not p:
        return ""
    return p if p.endswith(":") or p in ('"',) else (p + ":")

def build_queries(params_to_terms: Dict[str, List[str]], combine: bool = False) -> List[str]:
    """
    Build search queries from a dict like:
      { "site": ["docs.google.com", "forms.gle"], "intext": ["submit", "response"] }

    - If combine=False (default): build independent queries for each param-term (smaller set).
      e.g., ["site:docs.google.com", "site:forms.gle", "intext:submit", "intext:response"]

    - If combine=True: Cartesian product across all params (larger, more specific queries).
      e.g., ["site:docs.google.com intext:\"submit\"", "site:docs.google.com intext:\"response\"", ...]
    """
    if not params_to_terms:
        return []

    # Special handling: if user passes param "phrase", we wrap term in quotes and no trailing colon
    def render_pair(param: str, term: str) -> str:
        p = param.strip()
        t = term.strip()
        if not p:  # plain keyword
            return t
        if p.lower() == "phrase":
            return f"\"{t}\""
        pnorm = normalize_param(p)
        # Avoid double-colon like "site::"
        if pnorm == ":":
            return t
        return f"{pnorm}{t}"

    if not combine:
        queries = []
        for param, terms in params_to_terms.items():
            for term in terms:
                if term.strip():
                    queries.append(render_pair(param, term))
        # de-dup while preserving order
        seen = set()
        out = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                out.append(q)
        return out

    # combine=True
    # Build a list of lists, each inner list are rendered "param:term" parts for that param
    parts_per_param: List[List[str]] = []
    for param, terms in params_to_terms.items():
        rendered = [render_pair(param, t) for t in terms if t.strip()]
        if rendered:
            parts_per_param.append(rendered)

    if not parts_per_param:
        return []

    queries = []
    for combo in product(*parts_per_param):
        queries.append(" ".join(combo))
    # de-dup
    seen = set()
    out = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out
