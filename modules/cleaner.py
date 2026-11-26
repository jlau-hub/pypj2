import pandas as pd

COLUMNS = ["name", "category", "price", "stock", "url"]


def clean_products(raw_rows: list) -> pd.DataFrame:
    """去重、缺值處理、價格/類別正規化。"""
    df = pd.DataFrame(raw_rows, columns=COLUMNS)
    for col in ["name", "category", "stock", "url"]:
        df[col] = df[col].astype(str).str.strip()
    df["price"] = pd.to_numeric(
        df["price"].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")
    df["category"] = df["category"].str.replace(r"\s+", " ", regex=True)
    df = df.dropna(subset=["name", "price"])
    df = df[df["name"] != ""]
    df = df.drop_duplicates(subset=["name", "url"])
    return df.reset_index(drop=True)


def clean_articles(articles: list) -> list:
    seen, out = set(), []
    for a in articles:
        title = (a.get("title") or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        out.append({**a, "title": title, "content": (a.get("content") or "").strip()})
    return out
