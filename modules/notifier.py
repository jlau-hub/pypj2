import logging
from email.message import EmailMessage
from pathlib import Path
from datetime import date
from .config_loader import load_config

log = logging.getLogger(__name__)


def send_digest(report_path: Path, kpis: dict, insight: str, run_id: int):
    """生成 Email Digest 並儲存為 .eml 檔案 (Dry-run)"""
    cfg = load_config()["email"]

    msg = EmailMessage()
    # Include run_id in subject for easy identification
    msg["Subject"] = f"【MarketIntel】每日市場分析報告 {date.today():%Y-%m-%d} (Run {run_id})"
    msg["From"] = cfg.get("sender", "system@marketintel.local")
    msg["To"] = ", ".join(cfg.get("recipients", ["manager@example.com"]))

    body = (
        f"您好，\n\n"
        f"以下是今日 ({date.today():%Y-%m-%d}) 的市場數據摘要 (Run {run_id})：\n\n"
        f"📊 核心指標:\n"
        f"   - 總商品數: {kpis.get('total_items', 0)}\n"
        f"   - 平均價格: HK$ {kpis.get('avg_price', 0):,.0f}\n"
        f"   - 最大漲幅: {kpis.get('max_up', 'N/A')}\n\n"
        f"🤖 AI 市場洞察:\n{insight}\n\n"
        f"完整報告請見附件。\n\n"
        f"— MarketIntel Platform 自動發送 —"
    )
    msg.set_content(body)

    if report_path.exists():
        with open(report_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename=report_path.name,
            )

    out_dir = Path(load_config()["paths"]["reports"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # ✅ Include run_id in filename to prevent overwriting on same day
    eml_path = out_dir / f"digest_run{run_id}_{date.today():%Y%m%d}.eml"

    try:
        with open(eml_path, "wb") as f:
            f.write(bytes(msg))
        log.info("Digest saved to %s", eml_path)
        return eml_path
    except Exception as e:
        log.error("Failed to save digest: %s", e)
        return None