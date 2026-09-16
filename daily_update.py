from transformers import pipeline
from sources.scrapers import *
from sources.sentiment import ticker_sentiment, MODEL_NAME
from sources.data import init_db, store_sentiment
from sources.tickers import TICKERS

def main():
    init_db()
    model = pipeline("text-classification", model=MODEL_NAME)
    scraper = YahooScraper()

    for i, t in enumerate(TICKERS, 1):
        try:
            res = ticker_sentiment(t, scraper, model)
            if res:
                store_sentiment(res)
                print(f"[{i}/{len(TICKERS)}] {t} -> {res['label']}")
        except Exception as e:
            print(f"[{i}/{len(TICKERS)}] {t} FAILED: {e}")


if __name__ == "__main__":
    main()
