import time
from typing import Set

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def _collect_ddg_links(driver) -> Set[str]:
    links: Set[str] = set()

    # Prefer title links (more stable)
    anchors = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a'][href^='http']")
    if not anchors:
        # URL “extras” link
        anchors = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-extras-url-link'][href^='http']")
    if not anchors:
        # Fallback: anything inside results container
        anchors = driver.find_elements(By.CSS_SELECTOR, "ol.react-results--main a[href^='http']")

    for a in anchors:
        try:
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
    driver.get("https://duckduckgo.com/")

    # Wait until search box is clickable before typing
    search_box = WebDriverWait(driver, wait_secs).until(
        EC.element_to_be_clickable((By.NAME, "q"))
    )
    # Focus (sometimes needed for DDG overlays)
    driver.execute_script("arguments[0].focus();", search_box)
    time.sleep(0.1)
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    links: Set[str] = set()
    prev_height = 0
    stagnant_checks = 0

    while stagnant_checks < 3:
        try:
            # Wait for results container
            WebDriverWait(driver, wait_secs).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ol.react-results--main"))
            )

            # Collect links
            new_links = _collect_ddg_links(driver)
            links.update(new_links)

            # Try clicking "More results" when present
            more_btn = driver.find_elements(By.ID, "more-results")
            clicked = False
            if more_btn:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", more_btn[0])
                try:
                    WebDriverWait(driver, wait_secs).until(EC.element_to_be_clickable(more_btn[0]))
                    more_btn[0].click()
                    clicked = True
                except Exception:
                    pass

            # If no “More results”, scroll down to trigger lazy loads
            if not clicked:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(sleep_s)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == prev_height and not clicked:
                stagnant_checks += 1
            else:
                stagnant_checks = 0
            prev_height = new_height

        except Exception as e:
            print(f"[DuckDuckGo] {e}")
            break

    time.sleep(1.0)
    driver.quit()
    return links
