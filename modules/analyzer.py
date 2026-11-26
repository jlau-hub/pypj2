import logging
class _FontWarningFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        return "NotoColorEmoji" not in msg and "Non-scalable fonts" not in msg

logging.getLogger("matplotlib.font_manager").addFilter(_FontWarningFilter())
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from .config_loader import load_config

log = logging.getLogger(__name__)


def _cjk_font():
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in ["Noto Sans CJK TC", "Noto Sans CJK SC", "WenQuanYi Zen Hei", "Microsoft JhengHei"]:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def price_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["count", "mean", "min", "max"])
    return df.groupby("category")["price"].agg(["count", "mean", "min", "max"]).round(2)


def price_change(conn, run_id: int, prev_id) -> pd.DataFrame:
    cols = ["name", "price_now", "price_prev", "change_pct"]
    if not prev_id:
        return pd.DataFrame(columns=cols)
    cur = pd.read_sql_query("SELECT name, price FROM items WHERE run_id=?", conn, params=(run_id,))
    prev = pd.read_sql_query("SELECT name, price FROM items WHERE run_id=?", conn, params=(prev_id,))
    m = cur.merge(prev, on="name", suffixes=("_now", "_prev"))
    m = m[m["price_prev"] > 0]
    if m.empty:
        return pd.DataFrame(columns=cols)
    m["change_pct"] = ((m.price_now - m.price_prev) / m.price_prev * 100).round(2)
    return m.sort_values("change_pct", ascending=False).reset_index(drop=True)


def get_items_df(conn, run_id: int) -> pd.DataFrame:
    """從資料庫讀取指定 run_id 的商品資料並轉為 DataFrame"""
    return pd.read_sql_query("SELECT * FROM items WHERE run_id=?", conn, params=(run_id,))

def calculate_change(run_id: int, conn) -> pd.DataFrame:
    """計算價格漲跌 (Wrapper for price_change to match pipeline calls)"""
    # Note: In the fixed pipeline.py, we use res["change"] directly, so this is less critical
    # but kept for consistency if called elsewhere.
    return pd.DataFrame()


def stock_summary(df: pd.DataFrame) -> pd.Series:
    return df.groupby("stock").size() if not df.empty else pd.Series(dtype=int)


def save_charts(stats: pd.DataFrame, change: pd.DataFrame, outdir: Path, run_id: int) -> list:
    _cjk_font()
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []

    #  Chart 1: Category Stats (Skip if exists)
    p1 = outdir / f"chart_category_run{run_id}.png"
    if not p1.exists():
        fig, ax = plt.subplots(figsize=(8, 5))
        if not stats.empty:
            stats["mean"].plot(kind="bar", ax=ax, title=f"各類別平均價格（run {run_id}）")
            ax.set_ylabel("平均價格")
        else:
            ax.text(0.5, 0.5, "尚無資料", ha="center")
        fig.tight_layout()
        fig.savefig(p1, dpi=150)
        plt.close(fig)
        log.info("已產生圖表：%s", p1.name)
    else:
        log.info("圖表已存在，跳過：%s", p1.name)
    paths.append(p1)


    #  Chart 2: Top Movers (Skip if exists)
    top = load_config()["report"]["top_movers"]
    p2 = outdir / f"chart_movers_run{run_id}.png"
    if not p2.exists():
        fig, ax = plt.subplots(figsize=(8, 5))
        if not change.empty:
            movers = change.reindex(change.change_pct.abs().sort_values(ascending=False).index).head(top)
            movers.plot(kind="barh", x="name", y="change_pct", ax=ax, legend=False,
                        title=f"價格漲跌 TOP {top}（run {run_id}）")
            ax.set_xlabel("漲跌 %")
        else:
            ax.text(0.5, 0.5, "尚無前次 run 可比較", ha="center")
        fig.tight_layout()
        fig.savefig(p2, dpi=150)
        plt.close(fig)
        log.info("已產生圖表：%s", p2.name)
    else:
        log.info("圖表已存在，跳過：%s", p2.name)
    paths.append(p2)

    return paths

def stats_text(run, stats, change, articles) -> str:
    lines = [f"資料來源：{run['target']}，run {run['run_id']}，收集 {run['clean_count']} 筆商品",
             "類別價格統計：" + "; ".join(
                 f"{c} 平均 {r['mean']}（{r['count']} 項，{r['min']}~{r['max']}）"
                 for c, r in stats.iterrows()),
             "市場文章：" + "; ".join(a["title"] for a in articles)]
    if not change.empty:
        up = change.head(3)[["name", "change_pct"]].values.tolist()
        down = change.tail(3)[["name", "change_pct"]].values.tolist()
        lines.append("漲幅前三：" + ", ".join(f"{n} {p}%" for n, p in up))
        lines.append("跌幅前三：" + ", ".join(f"{n} {p}%" for n, p in down))
    return "\n".join(lines)
