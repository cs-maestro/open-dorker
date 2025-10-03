import time
from typing import Set

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def _maybe_accept_google_consent(driver, wait_secs: int = 10):
    """
    Try to click Google's consent/accept buttons (multi-lingual fallbacks).
    If nothing is found, silently continue.
    """
    try:
        WebDriverWait(driver, wait_secs).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except Exception:
        return

    selectors = [
        # Common consent buttons
        "//button[.//div[contains(text(),'I agree') or contains(text(),'Accept all')]]",
        "//button[contains(., 'I agree') or contains(., 'Accept all') or contains(., 'Accept')]",
        # Some regions use an overlay with role button
        "//div[@role='none']//button[contains(., 'I agree') or contains(., 'Accept')]",
        # Newer consent UI (2024+)
        "//button[contains(@aria-label,'Accept all')]",
    ]
    for xp in selectors:
        try:
            btns = driver.find_elements(By.XPATH, xp)
            if btns:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btns[0])
                WebDriverWait(driver, wait_secs).until(EC.element_to_be_clickable(btns[0]))
                btns[0].click()
                time.sleep(0.3)
                return
        except Exception:
            pass


def _collect_links_from_results(driver) -> Set[str]:
    links: Set[str] = set()

    # Primary (longstanding) organic layout
    cards = driver.find_elements(By.CSS_SELECTOR, "div.g")
    if not cards:
        # Newer container
        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-sokoban-container]")
    if not cards:
        # Fallback to main area search
        cards = driver.find_elements(By.CSS_SELECTOR, "div#search div")

    for card in cards:
        try:
            # Preferred: direct title link container
            a = None
            try:
                a = card.find_element(By.CSS_SELECTOR, "div.yuRUbf > a[href^='http']")
            except Exception:
                pass
            if a is None:
                # Fallback: any anchor with http and a data-ved (often present on result links)
                anchors = card.find_elements(By.CSS_SELECTOR, "a[href^='http']")
                for cand in anchors:
                    href = cand.get_attribute("href") or ""
                    # Filter obvious non-result links (cached, translate can still be ok; keep broad)
                    if href.startswith("http"):
                        a = cand
                        break

            if a:
                href = a.get_attribute("href") or ""
                if href.startswith("http"):
                    links.add(href)
        except Exception:
            continue

    return links


def search_and_scroll(query: str, headless: bool = False, wait_secs: int = 12, sleep_s: float = 0.6) -> Set[str]:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.google.com/")

    _maybe_accept_google_consent(driver, wait_secs=wait_secs)

    # Wait for the search box to be clickable and interact with it
    search_box = WebDriverWait(driver, wait_secs).until(
        EC.element_to_be_clickable((By.NAME, "q"))
    )
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    links: Set[str] = set()
    prev_len = 0
    stagnant_checks = 0

    while stagnant_checks < 3:
        try:
            WebDriverWait(driver, wait_secs).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div#search"))
            )

            # Collect from current page
            new_links = _collect_links_from_results(driver)
            links.update(new_links)

            # Handle Recaptcha (manual)
            recaptcha = driver.find_elements(By.XPATH, "//div[@id='recaptcha' and contains(@class,'g-recaptcha')]")
            if recaptcha:
                print("ReCAPTCHA detected. Solve it in the browser, then press Enter here to continue.")
                input("Press Enter after solving ReCAPTCHA...")

            # Pagination / more results
            clicked = False

            # 1) ‘More results’ button (mobile-like infinite)
            more = driver.find_elements(
                By.XPATH, "//span[contains(text(),'More results') and not(contains(text(),'More results from'))]"
            )
            if more:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", more[0])
                try:
                    WebDriverWait(driver, wait_secs).until(EC.element_to_be_clickable(more[0]))
                    more[0].click()
                    clicked = True
                except Exception:
                    pass

            # 2) “Next” button classic pagination
            if not clicked:
                next_btn = driver.find_elements(By.ID, "pnnext")
                if not next_btn:
                    next_btn = driver.find_elements(By.XPATH, "//a[@aria-label='Next page' or @id='pnnext']")
                if next_btn:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn[0])
                    try:
                        WebDriverWait(driver, wait_secs).until(EC.element_to_be_clickable(next_btn[0]))
                        next_btn[0].click()
                        clicked = True
                    except Exception:
                        pass

            # 3) As a last resort, scroll to bottom to trigger lazy-load UI
            if not clicked:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(sleep_s)

            if len(links) == prev_len:
                stagnant_checks += 1
            else:
                stagnant_checks = 0
            prev_len = len(links)

        except Exception as e:
            print(f"[Google] {e}")
            break

    time.sleep(1.5)
    driver.quit()
    return links
