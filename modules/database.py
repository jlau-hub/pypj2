import json
import sqlite3
from pathlib import Path
import pandas as pd
from .config_loader import load_config, ROOT


def get_conn():
    db_path = Path(load_config()["paths"]["database"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    with open(ROOT / "schema.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def start_run(conn, target: str) -> int:
    cur = conn.execute(
        "INSERT INTO runs(target, started_at, status) VALUES(?,datetime('now','localtime'),'running')",
        (target,))
    conn.commit()
    return cur.lastrowid


def finish_run(conn, run_id, pages, raw_count, clean_count, status, detail=""):
    conn.execute(
        """UPDATE runs SET finished_at=datetime('now','localtime'), pages=?, raw_count=?,
           clean_count=?, status=?, detail=? WHERE run_id=?""",
        (pages, raw_count, clean_count, status, detail, run_id))
    conn.commit()


def insert_raw(conn, run_id, rows):
    conn.executemany(
        "INSERT INTO raw_items(run_id, row_json, created_at) VALUES(?,?,datetime('now','localtime'))",
        [(run_id, json.dumps(r, ensure_ascii=False)) for r in rows])
    conn.commit()


def insert_items(conn, run_id, source, df):
    conn.executemany(
        """INSERT INTO items(run_id, source, name, category, price, stock, url, scraped_at)
           VALUES(?,?,?,?,?,?,?,datetime('now','localtime'))""",
        [(run_id, source, r.name, r.category, float(r.price), r.stock, r.url)
         for r in df.itertuples(index=False)])
    conn.commit()


def insert_articles(conn, run_id, source, articles):
    conn.executemany(
        """INSERT INTO articles(run_id, source, title, url, published, content, summary, scraped_at)
           VALUES(?,?,?,?,?,?,?,datetime('now','localtime'))""",
        [(run_id, source, a["title"], a["url"], a["published"], a["content"], a.get("summary", ""))
         for a in articles])
    conn.commit()


def get_run(conn, run_id):
    return conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()


def latest_run_id(conn):
    row = conn.execute(
        "SELECT run_id FROM runs WHERE status='ok' ORDER BY run_id DESC LIMIT 1").fetchone()
    return row["run_id"] if row else None


def previous_run_id(conn, run_id, target):
    row = conn.execute(
        """SELECT run_id FROM runs WHERE status='ok' AND target=? AND run_id<?
           ORDER BY run_id DESC LIMIT 1""", (target, run_id)).fetchone()
    return row["run_id"] if row else None


def get_items_df(conn, run_id):
    return pd.read_sql_query("SELECT * FROM items WHERE run_id=?", conn, params=(run_id,))


def get_articles(conn, run_id):
    return conn.execute("SELECT * FROM articles WHERE run_id=? ORDER BY article_id",
                        (run_id,)).fetchall()


def list_runs(conn, limit=10):
    return conn.execute("SELECT * FROM runs ORDER BY run_id DESC LIMIT ?", (limit,)).fetchall()
