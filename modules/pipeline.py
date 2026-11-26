import logging
from pathlib import Path
from . import (database as db, browser, scraper, cleaner, analyzer,
               ai_engine, report_builder, notifier)
from .config_loader import load_config

log = logging.getLogger(__name__)  # ✅ Fixed: was getLogger(name)

def run_target(target: dict) -> dict:
    conn = db.get_conn()
    run_id = db.start_run(conn, target["name"])
    pages, raw, df, arts = 0, [], None, []
    try:
        if not scraper.robots_allowed(target["start_url"]):
            db.finish_run(conn, run_id, 0, 0, 0, "blocked", "robots.txt 禁止收集")
            log.warning("robots.txt 禁止：%s", target["name"])
            return {"run_id": run_id, "status": "blocked"}
        
        session = (browser.login_and_session(target) if target.get("login_url")
                   else browser.plain_session())
        raw, pages = scraper.collect_products(session, target)
        db.insert_raw(conn, run_id, raw)
        df = cleaner.clean_products(raw)
        db.insert_items(conn, run_id, target["name"], df)
        
        arts = cleaner.clean_articles(scraper.collect_articles(session, target))
        arts = ai_engine.summarize_articles(arts)
        db.insert_articles(conn, run_id, target["name"], arts)
        
        db.finish_run(conn, run_id, pages, len(raw), len(df), "ok", f"articles={len(arts)}")
        log.info("run %d 完成：%d 頁 / 原始 %d / 清洗 %d / 文章 %d",
                 run_id, pages, len(raw), len(df), len(arts))
        return {"run_id": run_id, "status": "ok", "pages": pages,
                "raw": len(raw), "clean": len(df), "articles": len(arts)}
    except Exception as e:
        db.finish_run(conn, run_id, pages, len(raw), len(df) if df is not None else 0,
                      "error", str(e))
        log.exception("run %d 失敗：%s", run_id, e)
        raise
    finally:
        conn.close()

def analyze_run(run_id: int) -> dict:
    conn = db.get_conn()
    run = db.get_run(conn, run_id)
    if run is None:
        conn.close()
        raise ValueError(f"查無 run {run_id}")
    
    df = db.get_items_df(conn, run_id)
    prev = db.previous_run_id(conn, run_id, run["target"])
    stats = analyzer.price_stats(df)
    change = analyzer.price_change(conn, run_id, prev)
    articles = db.get_articles(conn, run_id)
    conn.close()
    
    outdir = Path(load_config()["paths"]["reports"])
    charts = analyzer.save_charts(stats, change, outdir, run_id)
    insight = ai_engine.market_insight(analyzer.stats_text(run, stats, change, articles))
    
    return {"run": run, "df": df, "stats": stats, "change": change,
            "articles": articles, "charts": charts, "insight": insight, "prev_run": prev}

def report_run(run_id: int) -> Path:
    res = analyze_run(run_id)
    report_path = report_builder.build_report(res)
    
    # --- 🚀 Email Digest Integration (FIXED FOR RE-RUN) ---
    try:
        kpis = {
            "total_items": len(res["df"]),
            "avg_price": float(res["df"]["price"].mean()) if "price" in res["df"].columns else 0,
            "max_up": f"{res['change']['name'].iloc[0]} (+{res['change']['change_pct'].iloc[0]}%)" 
                      if not res["change"].empty else "N/A"
        }
        # ✅ Pass run_id to preserve .eml per run; use res["insight"] instead of bare 'insight'
        notifier.send_digest(report_path, kpis, res["insight"], run_id)
    except Exception as e:
        log.warning("Email digest generation failed: %s", e)
    # -------------------------------------------
    
    return report_path

def run_all() -> list:
    results = []
    for target in load_config()["targets"]:
        r = run_target(target)
        if r.get("status") == "ok":
            r["report"] = str(report_run(r["run_id"]))
            results.append(r)
    return results