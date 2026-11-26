import json
import logging
import requests
from .config_loader import load_config

log = logging.getLogger(__name__)


def _post(payload: dict) -> str:
    cfg = load_config()["ai"]
    r = requests.post(cfg["base_url"].rstrip("/") + "/api/chat",
                      json=payload, timeout=(10, cfg["timeout"])
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def _call(prompt: str, temperature: float = 0, num_predict=None, fmt=None) -> str:
    cfg = load_config()["ai"]
    payload = {
        "model": cfg["model"],
        "stream": False,
        "keep_alive": cfg.get("keep_alive", "30m"),
        "options": {
            "temperature": temperature if temperature is not None else cfg.get("temperature", 0.2),
            "num_predict": num_predict or cfg.get("num_predict", 500),
            "num_ctx": cfg.get("num_ctx", 2048),
            "num_gpu": cfg.get("num_gpu", 0),
            "num_parallel": cfg.get("num_parallel", 0)
        },
        "messages": [{"role": "user", "content": prompt}],
    }
    if fmt:
        payload["format"] = fmt
    last = None
    for _ in range(cfg.get("retries", 1) + 1):
        try:
            return _post(payload)
        except Exception as e:
            last = e
    raise RuntimeError(f"Ollama 呼叫失敗：{last}")


def summarize_articles(articles: list) -> list:
    """一次呼叫摘要全部文章（4 次 → 1 次），失敗則逐篇截取備援。"""
    if not articles:
        return articles
    listing = "\n".join(
        f"{i+1}. {a['title']}\n{a['content'][:400]}" for i, a in enumerate(articles))
    prompt = ("請為以下每篇市場新聞各寫 60-80 字繁體中文摘要，"
              '只回傳 JSON：{"summaries": ["第1篇摘要", "第2篇摘要", ...]}\n' + listing)
    try:
        data = json.loads(_call(prompt, 0.2, num_predict=500, fmt="json"))
        sums = data.get("summaries", [])
        for i, a in enumerate(articles):
            a["summary"] = (sums[i] if i < len(sums) and sums[i]
                            else (a["content"][:120] + "…"))
    except Exception as e:
        log.warning("批次摘要失敗，改用截取備援：%s", e)
        for a in articles:
            a["summary"] = (a["content"][:120] + "…") if a["content"] else a["title"]
    return articles

def market_insight(stats_text: str) -> str:
    prompt = ("你是市場競爭分析師。根據以下收集與統計數據，用 300-400 字內繁體中文寫出競爭洞察"
              "與定價／採購建議：\n" + stats_text)
    try:
        return _call(prompt, 0.2, num_predict=500)
    except Exception as e:
        log.warning("洞察 AI 失敗，改用模板備援：%s", e)
        return ("建議持續監控價格波動最大之品項，檢視其類別平均價格與庫存狀態，"
                "作為定價與促銷策略參考；並追蹤市場新聞所述之成本與需求變化。")
# return _call(prompt, 0.3, num_predict=500)
