from transformers import pipeline
from sources.scrapers import YahooScraper, NewsScraper


def ticker_sentiment(ticker: str, scraper: NewsScraper) -> dict:
    finbert = pipeline("text-classification", model="ProsusAI/finbert")
    pages = scraper.fetch("AAPL", 100)
    sentiment = {"ticker": ticker, "articles": pages}

    count = 0
    for page in pages:
        result = finbert(page.get("title") + "." + page.get("summary"), truncation=True)[0]
        if result.get("label") == "positive":
            count += result.get("score")
        elif result.get("label") == "negative":
            count -= result.get("score")

    
    total_score = count / len(pages)
    sentiment["score"] = total_score 
    
    if total_score >= 0.15:
        sentiment["rating"] = "bullish"
    elif total_score <= -0.15:
        sentiment["rating"] = "bearish"
    else:
        sentiment["rating"] = "neutral"
    
    return sentiment


if __name__ == "__main__":
    scraper = YahooScraper()
    print(ticker_sentiment("AAPL", scraper))
    