import argparse
from pathlib import Path
from modules.config_loader import load_config, setup_logging
from modules import database as db


def cmd_init(args):
    cfg = load_config()
    for key, val in cfg["paths"].items():
        p = Path(val)
        (p.parent if key == "database" else p).mkdir(parents=True, exist_ok=True)
    db.init_db()
    print("初始化完成：目錄與資料庫已建立")


def cmd_run(args):
    from modules.pipeline import run_all
    for r in run_all():
        print(r)


def cmd_scrape(args):
    from modules.pipeline import run_target
    for t in load_config()["targets"]:
        print(run_target(t))


def _resolve_run(args):
    if getattr(args, "run", None):
        return args.run
    conn = db.get_conn()
    rid = db.latest_run_id(conn)
    conn.close()
    if not rid:
        raise SystemExit("尚無成功的 run，請先執行 python main.py run")
    return rid


def cmd_analyze(args):
    from modules.pipeline import analyze_run
    res = analyze_run(_resolve_run(args))
    print(f"run {res['run']['run_id']}（前次 {res['prev_run'] or '無'}）")
    print("\n[類別價格統計]\n", res["stats"].to_string())
    print("\n[價格漲跌]\n", res["change"].head(10).to_string(index=False))
    print("\n[AI 市場洞察]\n", res["insight"])


def cmd_report(args):
    from modules.pipeline import report_run
    print("報告：", report_run(_resolve_run(args)))


def cmd_runs(args):
    conn = db.get_conn()
    rows = db.list_runs(conn)
    conn.close()
    if not rows:
        print("尚無 run 記錄")
    for r in rows:
        print(f"[{r['run_id']}] {r['target']} {r['status']} pages={r['pages']} "
              f"raw={r['raw_count']} clean={r['clean_count']} {r['started_at']} {r['detail']}")


def main():
    setup_logging()
    p = argparse.ArgumentParser(description="網站資料自動收集與分析平台")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    sub.add_parser("run").set_defaults(fn=cmd_run)
    sub.add_parser("scrape").set_defaults(fn=cmd_scrape)
    a = sub.add_parser("analyze")
    a.add_argument("--run", type=int)
    a.set_defaults(fn=cmd_analyze)
    r = sub.add_parser("report")
    r.add_argument("--run", type=int)
    r.set_defaults(fn=cmd_report)
    sub.add_parser("runs").set_defaults(fn=cmd_runs)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
