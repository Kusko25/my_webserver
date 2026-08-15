from .rfeed import Item, Feed, Guid
from bs4 import BeautifulSoup
import datetime
import requests

from django.http import HttpResponse

class StarTrekLowerDecks2024:
    last_update = None
    items = []
    url = "https://readcomiconline.li/Comic/Star-Trek-Lower-Decks-2024"
    
    @classmethod
    def _fetch_html(cls):
        return requests.get(url=cls.url).text
    
    @classmethod
    def _update_rss(cls):
        try:
            items = []
            soup = BeautifulSoup(cls._fetch_html(), 'html.parser')
            for row in soup.find("ul",class_="list").find_all("li"):
                title, pubDate = [entry for entry in row.find_all("div")]
                title = title.find("a")
                assert title is not None
                href = title.get("href")
                href = f"https://readcomiconline.li{href}"
                title = title.find("span")
                assert title is not None
                title = title.text.strip()
                pubDate = pubDate.find("span")
                assert pubDate is not None
                pubDate = pubDate.text.strip()
                pubDate = pubDate.split("/")
                pubDate = [int(pubDate[2]),int(pubDate[0]), int(pubDate[1])]
                pubDate = datetime.datetime(*pubDate)
                items.append(Item(
                    title=title,
                    link=href,
                    author="Html scrape to rss",
                    guid=Guid(href),
                    pubDate=pubDate
                ))
            cls.items = items
            cls.last_update = datetime.datetime.now()
        except Exception as e:
            print("Failed to update RSS", e)
    
    @classmethod
    def rss(cls):
        if cls.last_update and (datetime.datetime.now() - cls.last_update) < datetime.timedelta(days=1):
            pass
        else:
            cls._update_rss()
        return Feed(
            title = "Star Trek: Lower Decks (2024)",
            link = "https://readcomiconline.li/Comic/Star-Trek-Lower-Decks-2024",
            description = "Hot off their Eisner nomination for Lower Decks tie-in Shax's Best Day, stellar duo Ryan North and Derek Charm are kicking off a brand-new ongoing series that's a big fun adventure on a big fun ship... wherein Dr. T'Ana saves the crew from a virulent, purple-boiled disease that is sure to — Wait, no, everyone's cured pretty quickly, actually. Okay... wherein Deep Space 2's distress call is mysteriously cut off and the crew has to — Wait, nope, they just needed some help resetting their comms systems. ALL RIGHT, WHEREIN Mariner gets so totally frustrated with the lack of thrills aboard the Cerritos that she drags her friends into a holodeck adventure that would definitely kill them in reality! Should totally provide them all with a sense of purpose and well-being, right? Right. Or at least it would have. If the U.S.S. Bonaventure hadn't shown back up from the Delta Triangle to provide them with a real challenge. It's time to explore a ghost ship, baby!",
            language = "en-US",
            lastBuildDate = datetime.datetime.now(),
            items = cls.items
        ).rss()
    
    @classmethod
    def view(cls, request):
        return HttpResponse("Offline. Run Over.",status=400)
        rss = cls.rss()
        return HttpResponse(rss, content_type='application/rss+xml; charset=utf-8')
