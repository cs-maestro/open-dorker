# Open Dorker — Interactive Google & DuckDuckGo Dorking to CSV

**Open Dorker** is a simple, interactive CLI tool for security researchers, OSINT analysts, and growth/marketing teams who want to **compose search-dorks** and export **`search_term,url`** pairs to CSV. Choose **Google** or **DuckDuckGo**, pick one or more **dork parameters** (e.g., `site`, `intext`, `intitle`, `inurl`, `filetype`, `ext`, `before`, `after`, `cache`, `related`), enter terms for each, and let the tool scroll, collect, and save.

> ⚠️ **Ethical & Legal Use Only**  
> Respect each search engine’s Terms of Service, robots policies, and local laws. Do **not** use this tool for illicit activity. The authors are not responsible for misuse.

---

## ✨ Features

- ✅ Interactive prompts: choose engine(s), dork parameters, and terms
- ✅ Uses **Selenium + Chrome**
- ✅ Handles “load more”/pagination and basic ReCAPTCHA prompts (manual solve)
- ✅ Exports **`search_term,url`** to a CSV (append-friendly)
- ✅ Headless mode optional (`--headless`)
- ✅ Works on macOS, Linux, Windows

---

## 🚀 Quick Start

### 1) Prereqs
- **Python 3.9+**
- **Google Chrome** (latest)

### 2) Install
```bash
git clone https://github.com/cs-maestro/open-dorker.git
cd open-dorker

python -m venv .venv
# Windows: 
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```
We use webdriver-manager to automatically fetch a matching ChromeDriver.

### 3) Run (interactive)

```bash
python -m open_dorker.cli
```
- Pick **Google, DuckDuckGo, or Both**
- Enter dork parameters (comma-separated), e.g.: _site_, _intext_, _intitle_
- For each parameter, enter terms (comma-separated), e.g. for site: _docs.google.com_, _forms.gle_, _forms.office.com_

CSV will be written to results.csv by default (customize with --out).

### 4) Run (power users)
```bash
python -m open_dorker.cli \
  --engine both \
  --params site,intext,intitle \
  --terms site="docs.google.com,forms.gle" intext="password reset,confidential" intitle="login,register" \
  --out my_results.csv \
  --headless
```

## 🧩 What dork params can I use?

Common (not exhaustive):
- site:domain.com
- intext:keyword
- intitle:keyword
- inurl:path-fragment
- filetype:pdf / ext:pdf
- before:YYYY-MM-DD / after:YYYY-MM-DD (Google)
- cache:domain.com (Google)
- "exact phrase" (use phrase param in this tool)

## 🔧 Troubleshooting

- **ReCAPTCHA on Google:** We pause and ask you to solve manually in the browser. Then press Enter in the terminal to continue.
- **No results / few links:** Try fewer params, add time between scrolls, or switch engines.
- **Selectors broke:** Search engines change markup occasionally. Update the CSS/XPath in engines/*.py if needed.

