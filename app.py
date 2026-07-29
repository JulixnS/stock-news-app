from fastapi import FastAPI
from sources.data import *
app = FastAPI()

@app.get("/")
def root():
    return "Hello World"

@app.get("/tickers/{ticker}")
def get_data(ticker: str):
    return read(ticker)

@app.get("/tickers/{ticker}/articles")
def articles(ticker, label: str | None = None):
    return get_articles(ticker, label)

@app.get("/picks")
def picks(limit:int = 10):
    return top_k_tickers(limit)
