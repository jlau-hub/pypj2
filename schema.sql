CREATE TABLE IF NOT EXISTS runs(
  run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  target      TEXT,
  started_at  TEXT,
  finished_at TEXT,
  pages       INTEGER DEFAULT 0,
  raw_count   INTEGER DEFAULT 0,
  clean_count INTEGER DEFAULT 0,
  status      TEXT,
  detail      TEXT
);
CREATE TABLE IF NOT EXISTS raw_items(
  raw_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id     INTEGER NOT NULL,
  row_json   TEXT,
  created_at TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(run_id)
);
CREATE TABLE IF NOT EXISTS items(
  item_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id     INTEGER NOT NULL,
  source     TEXT,
  name       TEXT,
  category   TEXT,
  price      REAL,
  stock      TEXT,
  url        TEXT,
  scraped_at TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(run_id)
);
CREATE TABLE IF NOT EXISTS articles(
  article_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id     INTEGER NOT NULL,
  source     TEXT,
  title      TEXT,
  url        TEXT,
  published  TEXT,
  content    TEXT,
  summary    TEXT,
  scraped_at TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(run_id)
);
CREATE INDEX IF NOT EXISTS idx_items_run  ON items(run_id);
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
CREATE INDEX IF NOT EXISTS idx_runs_target ON runs(target);
