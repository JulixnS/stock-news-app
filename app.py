from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sources.data import *


app = FastAPI()


@app.get("/tickers/{ticker}")
def get_data(ticker: str):
    return read(ticker)

@app.get("/tickers/{ticker}/articles")
def articles(ticker: str, label: str | None = None):
    return get_articles(ticker, label)

@app.get("/picks")
def picks(limit: int = 10):
    return top_k_tickers(limit)

@app.get("/tickers/{ticker}/history")
def history(ticker, limit: str |None = None):
    try:
        return get_history(ticker, limit)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"'{limit}' is not a valid date. Use YYYY-MM-DD (eg. 2026-7-15), or M/D/YY",
        )


# Serve the front-end. Mounted LAST so the API routes above win;
# html=True serves frontend/index.html at "/". Same origin as the API, so no CORS.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
