import os
import sqlite3
from datetime import datetime, timezone

# Database location. Defaults to the historical relative path so nothing
# changes for local runs; override in systemd/Docker with an absolute path.
DB_PATH = os.environ.get("DB_PATH", "database.db")

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS sentiments(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    time TEXT NOT NULL,
                    ticker TEXT NOT NULL, 
                    score REAL NOT NULL, 
                    label TEXT NOT NULL, 
                    articles INTEGER NOT NULL
                );
                """)
    

    cur.execute("""
                CREATE TABLE IF NOT EXISTS articles(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sentiments_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT, 
                    label TEXT,
                    summary TEXT,
                    score REAL,
                    FOREIGN KEY (sentiments_id) REFERENCES sentiments(id)
                );
                """)
    
    con.commit()
    con.close()
    print("Database Initialized")

def clear_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("DELETE FROM articles")      # children FIRST
    cur.execute("DELETE FROM sentiments")    # then parents
    cur.execute("DELETE FROM sqlite_sequence")  # reset AUTOINCREMENT counters

    con.commit()
    con.close()
    print("Database Cleared")




def store_sentiment(sentiment: dict) -> int:
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO sentiments(time, ticker, score, label, articles)
        VALUES(?,?,?,?,?)""",
        (datetime.now(timezone.utc).isoformat(), sentiment["ticker"], sentiment["score"], sentiment["label"], len(sentiment["articles"]))      
        )
    sentiments_id = cur.lastrowid

    for a in sentiment["articles"]:
        cur.execute("""
                    INSERT INTO articles(sentiments_id, url, title, label, summary, score) 
                    VALUES (?,?,?,?,?,?)""", 
                    (sentiments_id, a["url"], a["title"], a["label"], a["summary"], a["score"]))

    con.commit()
    con.close()
    print(f'{sentiment["ticker"]} inserted.')

def read(ticker: str):
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row          # rows behave like dicts -> named JSON
    cur =  con.cursor()

    row = cur.execute("SELECT * FROM sentiments WHERE ticker = ? ORDER BY time DESC LIMIT 1", (ticker,)).fetchone()

    if row is None:
        con.close()
        return None

    articles = con.execute("""
        SELECT * FROM articles WHERE sentiments_id = ? ORDER BY score DESC
    """, (row["id"],)).fetchall()
    
    res = dict(row)
    res["coverage"] = [dict(a) for a in articles]


    con.close()
    return res

def get_latest_id(ticker: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    res = cur.execute("SELECT * FROM sentiments WHERE ticker = ? ORDER BY id DESC LIMIT 1", (ticker,)).fetchall()[0]
    id = res[0]
    
    con.close()
    return id


def get_articles(ticker: str, label: str = None):
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row          # rows behave like dicts -> named JSON
    cur = con.cursor()
    latest_id = get_latest_id(ticker)

    if label is None:
        res = cur.execute("SELECT * FROM articles WHERE sentiments_id = ? ORDER BY score DESC", (latest_id,)).fetchall()
    else:
        res = cur.execute("SELECT * FROM articles WHERE sentiments_id = ? AND label = ? ORDER BY score DESC", (latest_id, label)).fetchall()
    con.close()

    return [dict(r) for r in res]

def top_k_tickers(k: int = 5, min_articles: int = 5):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row          # rows behave like dicts -> named JSON
    cur = con.cursor()
    res = cur.execute("""
        WITH latest AS (
            SELECT ticker, MAX(id) AS id FROM sentiments GROUP BY ticker
        )
        SELECT s.ticker, s.score, s.label, s.articles, s.time,
               SUM(CASE WHEN a.label = 'positive' THEN 1 ELSE 0 END) AS pos,
               SUM(CASE WHEN a.label = 'negative' THEN 1 ELSE 0 END) AS neg,
               SUM(CASE WHEN a.label = 'neutral'  THEN 1 ELSE 0 END) AS neu
        FROM sentiments s
        JOIN latest l ON s.id = l.id
        LEFT JOIN articles a ON a.sentiments_id = s.id
        WHERE s.articles >= ?
        GROUP BY s.id
        ORDER BY s.score DESC
        LIMIT ?
    """, (min_articles, k)).fetchall()
    con.close()
    return [dict(r) for r in res]

