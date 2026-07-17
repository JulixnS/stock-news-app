from abc import ABC, abstractmethod
import yfinance as yf
from helper import title_contains


# Blueprint for all scrapers
class NewsScraper(ABC):
    name: str

    @abstractmethod
    def fetch(self, ticker: str, n: int) -> list:
           pass



class YahooScraper(NewsScraper):
    
    name = "yahoo"
        
    def fetch(self, t: str, n: int) -> list:
        
        urls = [] #list of news articles to be returned
        
        ticker = yf.Ticker(t)
        news = ticker.get_news(count = n)
        
        for article in news:
            title = article.get("content").get("title")

            if(title_contains(title, t, ticker.info.get("longName"))):
                 urls.append(article.get("content").get("canonicalUrl").get("url"))

        return urls
            
            
             




if __name__ == "__main__":
    scraper = YahooScraper()
    urls = scraper.fetch("MRVL", 100)

    print(urls)