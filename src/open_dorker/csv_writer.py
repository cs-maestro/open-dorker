import csv
from pathlib import Path
from typing import Iterable, Tuple

def append_rows(rows: Iterable[Tuple[str, str, str]], csv_path: Path):
    """Append (search_term, url, engine) rows to a CSV with header if file is new."""
    new_file = not csv_path.exists()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["search_term", "url", "engine"])
        for term, url, eng in rows:
            w.writerow([term, url, eng])
