from sources.sentiment import ticker_sentiment
from sources.data import store_sentiment, init_db, read
from sources.scrapers import YahooScraper


if __name__ == "__main__":
    scraper = YahooScraper()
    res = ticker_sentiment("AAPL", scraper)
    init_db()
    store_sentiment(res)
    print(read("AAPL"))


