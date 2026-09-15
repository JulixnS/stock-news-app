from transformers import pipeline
from sources.scrapers import YahooScraper, NewsScraper
from sources.data import get_scored


def ticker_sentiment(ticker: str, scraper: NewsScraper, finbert) -> dict:
    pages = scraper.fetch(ticker, 100)
    if len(pages) == 0:
        return None

    sentiment = {"ticker": ticker, "articles": pages}

    count = 0
    already_scored = get_scored([p["url"] for p in pages])

    for page in pages:
        cached = already_scored.get(page["url"])   #get the url to see if it already has a score  
        if cached:
            label, score = cached   #if it does, keep the same label and score
        else:    #otherwise, call the model and score it
            result = finbert(page.get("title") + "." + page.get("summary"), truncation=True)[0]
            score = result["score"]
            label = result["label"]
        if label == "positive":
            count += score
        elif label == "negative":
            count -= score

        page["score"] = score   #set the label and scores in the page dict
        page["label"] = label

    total_score = count / len(pages)
    sentiment["score"] = total_score 
    
    if total_score >= 0.15:
        sentiment["label"] = "bullish"
    elif total_score <= -0.15:
        sentiment["label"] = "bearish"
    else:
        sentiment["label"] = "neutral"
    
    return sentiment   #{ticker, articles, score, label}


if __name__ == "__main__":
    finbert = pipeline("text-classification", model="ProsusAI/finbert")
    print(ticker_sentiment("AAPL", YahooScraper(), finbert))
    