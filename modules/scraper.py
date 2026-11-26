import logging
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from .config_loader import load_config

log = logging.getLogger(__name__)


def robots_allowed(url: str) -> bool:
    cfg = load_config()["scrape"]
    if not cfg.get("respect_robots", True):
        return True
    parts = urlsplit(url)
    rp = RobotFileParser(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        return True                      # 無 robots.txt 或連線失敗 → 視為未禁止
    return rp.can_fetch(cfg.get("user_agent", "*"), url)


def collect_products(session: requests.Session, target: dict):
    cfg = load_config()["scrape"]
    url, rows, pages = target["start_url"], [], 0
    while url and pages < cfg["max_pages"]:
        r = session.get(url, timeout=cfg["timeout"])
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tr in soup.select(target["row_selector"]):
            cells = [td.get_text(strip=True) for td in tr.select("td")]
            if cells:
                rows.append(cells)
        nxt = soup.select_one(target["next_selector"])
        url = urljoin(url, nxt["href"]) if nxt and nxt.get("href") else None
        pages += 1
        log.info("收集第 %d 頁：%s（累計 %d 筆）", pages, url or "結束", len(rows))
        time.sleep(cfg["delay"])
    return rows, pages


def collect_articles(session: requests.Session, target: dict) -> list:
    if not target.get("news_url"):
        return []
    cfg = load_config()["scrape"]
    r = session.get(target["news_url"], timeout=cfg["timeout"])
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for art in soup.select(target["article_selector"]):
        t = art.select_one(target["article_title_selector"])
        d = art.select_one(target["article_date_selector"])
        c = art.select_one(target["article_content_selector"])
        link = art.select_one("a")
        out.append({
            "title": t.get_text(strip=True) if t else "",
            "published": d.get_text(strip=True) if d else "",
            "content": c.get_text("\n", strip=True) if c else "",
            "url": urljoin(target["news_url"], link["href"]) if link and link.get("href")
                   else target["news_url"],
        })
    time.sleep(cfg["delay"])
    return out
