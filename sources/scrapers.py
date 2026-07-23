from abc import ABC, abstractmethod
import yfinance as yf
from sources.helper import title_contains
from sources.tickers import NAME_ALIASES


# Blueprint for all scrapers
class NewsScraper(ABC):
    name: str

    @abstractmethod
    def fetch(self, ticker: str, n: int) -> list:
           pass



class YahooScraper(NewsScraper):
    
    name = "yahoo"
        
    def fetch(self, t: str, n: int) -> list:
        
        pages = [] #list of news articles to be returned
        
        ticker = yf.Ticker(t)
        news = ticker.get_news(count = n)
        try:
            longName = ticker.info.get("longName")
        except Exception:
             longName = None

        # longName plus any headline-only trade names (Alphabet -> "Google").
        names = [longName, *NAME_ALIASES.get(t, [])]

        for article in news:
            title = article.get("content").get("title")

            if(title_contains(title, t, names)):
                 pages.append(
                      {"url": article.get("content").get("canonicalUrl").get("url"),
                       "title": title,
                       "summary": article.get("content").get("summary", "")
                      })

        return pages
            
            
             




if __name__ == "__main__":
    scraper = YahooScraper()
    urls = scraper.fetch("MRVL", 100)

    print(urls)