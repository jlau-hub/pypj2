import logging
from datetime import date
from pathlib import Path
from docx import Document
from docx.shared import Inches
from .config_loader import load_config

log = logging.getLogger(__name__)


def _table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        t.rows[0].cells[i].text = str(h)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
    return t


def build_report(res: dict) -> Path:
    run, stats, change = res["run"], res["stats"], res["change"]
    out = Path(load_config()["paths"]["reports"])
    out.mkdir(parents=True, exist_ok=True)
    doc = Document()
    doc.add_heading("市場情報自動分析報告", 0)
    doc.add_paragraph(f"報告日期：{date.today():%Y-%m-%d}　資料來源：{run['target']}　"
                      f"run：{run['run_id']}　前次比較 run：{res['prev_run'] or '無'}")

    doc.add_heading("一、收集概覽", 1)
    doc.add_paragraph(f"收集頁數 {run['pages']}；原始 {run['raw_count']} 筆；"
                      f"清洗後 {run['clean_count']} 筆；市場文章 {len(res['articles'])} 篇。")

    doc.add_heading("二、類別價格統計", 1)
    _table(doc, ["類別", "項數", "平均", "最低", "最高"],
           [[c, r["count"], r["mean"], r["min"], r["max"]] for c, r in stats.iterrows()])

    doc.add_heading("三、價格漲跌分析", 1)
    if change.empty:
        doc.add_paragraph("本次為首次收集，尚無前次 run 可比較。")
    else:
        top = load_config()["report"]["top_movers"]
        movers = change.reindex(change.change_pct.abs().sort_values(ascending=False).index).head(top)
        _table(doc, ["商品", "本次價格", "前次價格", "漲跌 %"],
               [[r.name, r.price_now, r.price_prev, r.change_pct]
                for r in movers.itertuples(index=False)])

    doc.add_heading("四、圖表", 1)
    for p in res["charts"]:
        if Path(p).exists():
            doc.add_picture(str(p), width=Inches(6.2))

    doc.add_heading("五、市場文章 AI 摘要", 1)
    for a in res["articles"]:
        doc.add_paragraph(f"{a['title']}（{a['published']}）", style="List Bullet")
        doc.add_paragraph(a["summary"] or "（無摘要）")

    doc.add_heading("六、AI 市場洞察", 1)
    doc.add_paragraph(res["insight"])

    doc.add_heading("七、合規與方法說明", 1)
    doc.add_paragraph("本報告資料以 Selenium 登入後之 session 收集，遵守 robots.txt 與"
                      "速率限制（每次請求間隔 1 秒），僅收集授權或公開練習用之目標網站；"
                      "原始資料保留於 raw_items 以供稽核。")

    path = out / f"市場分析報告_{date.today():%Y%m%d}_run{run['run_id']}.docx"
    doc.save(str(path))
    log.info("報告已產生：%s", path)
    return path
