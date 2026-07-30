from transformers import pipeline
from sources.scrapers import *
from sources.sentiment import ticker_sentiment
from sources.data import init_db, store_sentiment
from sources.tickers import TICKERS

def main():
    init_db()
    finbert = pipeline("text-classification", model="ProsusAI/finbert")
    scraper = YahooScraper()

    for i, t in enumerate(TICKERS, 1):
        try:
            res = ticker_sentiment(t, scraper, finbert)
            if res:
                store_sentiment(res)
                print(f"[{i}/{len(TICKERS)}] {t} -> {res['label']}")
        except Exception as e:
            print(f"[{i}/{len(TICKERS)}] {t} FAILED: {e}")


if __name__ == "__main__":
    main()
