from typing import Dict, List

def parse_terms_kv(pairs: List[str]) -> Dict[str, List[str]]:
    """
    Parse args like: ["site=docs.google.com,forms.gle", "intext=password,submit"]
    into { "site": ["docs.google.com","forms.gle"], "intext":["password","submit"] }
    """
    out: Dict[str, List[str]] = {}
    for item in pairs:
        if "=" not in item:
            continue
        key, vals = item.split("=", 1)
        key = key.strip()
        vals_list = [v.strip() for v in vals.split(",") if v.strip()]
        if key and vals_list:
            out[key] = vals_list
    return out

def prompt_list(prompt_text: str) -> List[str]:
    s = input(prompt_text).strip()
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]
