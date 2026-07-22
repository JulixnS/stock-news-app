import sqlite3
from datetime import datetime, timezone

def init_db():
    con = sqlite3.connect("database.db")
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




def store_sentiment(sentiment: dict) -> int:
    con = sqlite3.connect("database.db")
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

def read(ticker: str):
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    cur =  con.cursor()

    res = cur.execute("SELECT * FROM sentiments WHERE ticker = ? ORDER BY time DESC LIMIT 1", (ticker,)).fetchall()
    con.close()
    return res

def get_latest_id(ticker: str):
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    res = cur.execute("SELECT * FROM sentiments WHERE ticker = ? ORDER BY id DESC LIMIT 1", (ticker,)).fetchall()[0]
    id = res[0]
    
    con.close()
    return id


def get_articles(ticker: str, label: str = None):
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    latest_id = get_latest_id(ticker)

    if label is None:
        res = cur.execute("SELECT * FROM articles WHERE sentiments_id = ?", (latest_id,)).fetchall()
    else:
        res = cur.execute("SELECT * FROM articles WHERE sentiments_id = ? AND label = ?", (latest_id, label)).fetchall()
    con.close()

    return res