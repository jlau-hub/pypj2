import logging
from pathlib import Path
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .config_loader import load_config

log = logging.getLogger(__name__)


def _driver():
    cfg = load_config()["browser"]
    opts = Options()
    if cfg.get("headless", True):
        opts.add_argument("--headless=new")
    for arg in ["--no-sandbox", "--disable-dev-shm-usage", "--window-size=1400,900"]:
        opts.add_argument(arg)
    if cfg.get("binary_path"):
        opts.binary_location = cfg["binary_path"]
    if cfg.get("driver_path"):
        return webdriver.Chrome(service=Service(cfg["driver_path"]), options=opts)
    return webdriver.Chrome(options=opts)


def plain_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": load_config()["scrape"]["user_agent"]})
    return s


def login_and_session(target: dict) -> requests.Session:
    """Selenium 表單登入 → 驗證 → 截圖 → cookies 轉移至 requests.Session。"""
    cfg = load_config()
    driver = _driver()
    try:
        driver.get(target["login_url"])
        driver.find_element(By.NAME, target["user_field"]).send_keys(target["username"])
        driver.find_element(By.NAME, target["pass_field"]).send_keys(target["password"])
        driver.find_element(By.CSS_SELECTOR, target["submit_selector"]).click()
        WebDriverWait(driver, cfg["browser"]["login_timeout"]).until(
            EC.url_contains(target["login_success_marker"]))
        shot = Path(cfg["paths"]["logs"]) / f"login_{target['name']}.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(shot))
        log.info("登入成功：%s（截圖 %s）", target["name"], shot)
        s = plain_session()
        for c in driver.get_cookies():
            s.cookies.set(c["name"], c["value"])
        return s
    finally:
        driver.quit()
