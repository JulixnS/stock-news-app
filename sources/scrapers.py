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
        news = ticker.get_news(count = n) or []    #list of all the news articles related to the company
        try:
            longName = ticker.info.get("longName")
        except Exception:
            longName = None
            print(f"{t}: could not get longname, searching for articles only containing {t}")

        # longName plus any headline-only trade names (Alphabet -> "Google").
        names = [longName, *NAME_ALIASES.get(t, [])]

        for article in news:
            content = article.get("content") or {} # if articles.get() returns none, just make it an empty dict
            title = content.get("title")

            if not title:
                continue   #if there is no article, skip and move onto the next
            
            if(title_contains(title, t, names)):   #Check if the article has the company's name in it, we only want articles about that company
                link = (content.get("canonicalUrl") or {}).get("url") #get the url of the article
                if not link:  #if no link, skip the entry
                    continue
                
                pages.append(
                    {"url": link,
                    "title": title,
                    "summary": content.get("summary") or ""
                    })

        return pages


if __name__ == "__main__":
    scraper = YahooScraper()
    urls = scraper.fetch("MRVL", 100)

    print(urls)