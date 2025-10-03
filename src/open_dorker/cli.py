import argparse
from pathlib import Path
from typing import Dict, List, Tuple

from .dork_builder import build_queries
from .csv_writer import append_rows
from .utils import parse_terms_kv, prompt_list

from .engines.google_scrape import search_and_scroll as google_search
from .engines.duckduckgo_scrape import search_and_scroll as ddg_search

def run_interactive() -> Tuple[str, Dict[str, List[str]], bool]:
    # Engine
    engine = ""
    while engine not in ("google", "duckduckgo", "both"):
        engine = input("Choose engine [google/duckduckgo/both]: ").strip().lower()

    # Params
    params = prompt_list("Enter dork parameters (comma-separated, e.g. site,intext,intitle): ")
    if not params:
        print("No parameters provided. You can also use 'phrase' for exact quotes or leave blank for raw keywords.")
        params = prompt_list("Enter dork parameters (or leave blank): ")

    # Terms per param
    params_to_terms: Dict[str, List[str]] = {}
    for p in params:
        terms = prompt_list(f'Enter terms for "{p}" (comma-separated): ')
        params_to_terms[p] = terms

    # Optional raw keywords without any param (param="")
    raw_terms = prompt_list("Any raw keywords (no param, comma-separated)? (optional): ")
    if raw_terms:
        params_to_terms[""] = raw_terms

    # Combine?
    combine_answer = input("Combine across params (Cartesian product)? [y/N]: ").strip().lower()
    combine = combine_answer in ("y", "yes")

    return engine, params_to_terms, combine

def main():
    parser = argparse.ArgumentParser(
        description="Open Dorker — Interactive Google & DuckDuckGo dorking to CSV"
    )
    parser.add_argument("--engine", choices=["google", "duckduckgo", "both"])
    parser.add_argument("--params", help="Comma-separated params (e.g., site,intext,intitle)")
    parser.add_argument("--terms", nargs="*", default=[], help='Pairs like site="a,b" intext="x,y" phrase="exact text"')
    parser.add_argument("--out", default="results.csv", help="Output CSV path")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--combine", action="store_true", help="Combine across params (Cartesian product)")
    args = parser.parse_args()

    if not (args.engine and (args.params or args.terms)):
        print("Entering interactive mode...\n")
        engine, params_to_terms, combine = run_interactive()
        out_path = Path("results.csv")
        headless = False
    else:
        engine = args.engine
        params_to_terms = {}
        # params list
        if args.params:
            for p in [x.strip() for x in args.params.split(",") if x.strip()]:
                params_to_terms.setdefault(p, [])
        # kv terms
        kv = parse_terms_kv(args.terms)
        for k, vlist in kv.items():
            params_to_terms.setdefault(k, [])
            params_to_terms[k].extend(vlist)
        combine = args.combine
        out_path = Path(args.out)
        headless = args.headless

    # Build queries
    queries = build_queries(params_to_terms, combine=combine)
    if not queries:
        print("No queries built. Exiting.")
        return

    print(f"Total queries: {len(queries)}")
    all_rows: List[Tuple[str, str, str]] = []

    def run_engine(name: str, q: str) -> List[str]:
        if name == "google":
            return list(google_search(q, headless=headless))
        elif name == "duckduckgo":
            return list(ddg_search(q, headless=headless))
        else:
            raise ValueError("Unknown engine")

    engines_to_run = []
    if engine == "both":
        engines_to_run = ["google", "duckduckgo"]
    else:
        engines_to_run = [engine]

    for q in queries:
        for eng in engines_to_run:
            print(f"\n[{eng.upper()}] Running: {q}")
            try:
                links = run_engine(eng, q)
                print(f"Found {len(links)} links.")
                all_rows.extend((q, url, eng) for url in links)
            except Exception as e:
                print(f"[{eng}] Error: {e}")

    append_rows(all_rows, Path(out_path))
    print(f"\nDone. Wrote {len(all_rows)} rows to: {out_path}")

if __name__ == "__main__":
    main()
