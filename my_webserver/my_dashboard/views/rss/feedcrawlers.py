from .rfeed import Item, Feed, Guid
from bs4 import BeautifulSoup, Tag
import datetime
import requests

from django.http import HttpResponse
from django.utils.timezone import get_default_timezone as tz, now

def nullCheck(tag: Tag | None, func = lambda x: x.text):
    if isinstance(tag,Tag):
        return func(tag)
    else:
        return "null"

class RSSView:
    ENABLED = True
    disabled_message = "Offline. Run Over."
    last_update = None
    items = []
    url = "https://readcomiconline.li/Comic/Star-Trek-Lower-Decks-2024"
    title = "Star Trek: Lower Decks (2024)"
    link = "https://readcomiconline.li/Comic/Star-Trek-Lower-Decks-2024"
    description = (
        "Hot off their Eisner nomination for Lower Decks tie-in Shax's Best Day, stellar duo " \
        "Ryan North and Derek Charm are kicking off a brand-new ongoing series that's a big fun " \
        "adventure on a big fun ship... wherein Dr. T'Ana saves the crew from a virulent, purple-boiled " \
        "disease that is sure to — Wait, no, everyone's cured pretty quickly, actually. Okay... wherein " \
        "Deep Space 2's distress call is mysteriously cut off and the crew has to — Wait, nope, they just " \
        "needed some help resetting their comms systems. ALL RIGHT, WHEREIN Mariner gets so totally " \
        "frustrated with the lack of thrills aboard the Cerritos that she drags her friends into a " \
        "holodeck adventure that would definitely kill them in reality! Should totally provide them " \
        "all with a sense of purpose and well-being, right? Right. Or at least it would have. " \
        "If the U.S.S. Bonaventure hadn't shown back up from the Delta Triangle to provide them with a " \
        "real challenge. It's time to explore a ghost ship, baby!")
    language = "en-US"
    
    @classmethod
    def _fetch_html(cls):
        return requests.get(url=cls.url).text
    
    @classmethod
    def _update_rss(cls):
        try:
            items = []
            soup = BeautifulSoup(cls._fetch_html(), 'html.parser')
            list = soup.find("ul",class_="list")
            assert list is not None
            
            for row in list.find_all("li"):
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
                pubDate = datetime.datetime(*pubDate, tzinfo=tz())
                items.append(Item(
                    title=title,
                    link=href,
                    author="Html scrape to rss",
                    guid=Guid(href),
                    pubDate=pubDate
                ))
            cls.items = items
            cls.last_update = now()
        except Exception as e:
            print("Failed to update RSS", e)
    
    @classmethod
    def rss(cls):
        if cls.last_update and (now() - cls.last_update) < datetime.timedelta(days=1):
            pass
        else:
            cls._update_rss()
        return Feed(
            title = cls.title,
            link = cls.link,
            description = cls.description,
            language = cls.language,
            lastBuildDate = now(),
            items = cls.items
        ).rss()
    
    @classmethod
    def view(cls, request):
        if not cls.ENABLED:
            return HttpResponse(cls.disabled_message,status=400)
        rss = cls.rss()
        return HttpResponse(rss, content_type='application/rss+xml; charset=utf-8')

class StarTrekLowerDecks2024(RSSView):
    ENABLED = False

class SVSComics(RSSView):
    title = "SVSComics - Porn Comics & Sex Games"
    url = "https://svscomics.com/"
    link = "https://svscomics.com/"
    description = (
        "Join 250,000+ members at SVSComics for free premium adult games and sex comics. Access high-quality 18+ " \
        "content via verified Keep2share, Fileboom, and Florenfile links updated daily")
    language = "en-US"
    
    @classmethod
    def _update_rss(cls):
        try:
            items = []
            soup = BeautifulSoup(cls._fetch_html(), 'html.parser')
            
            for post in soup.select('article.post'):
                title = nullCheck(post.select_one('div.header-title'))
                pubDate = post.select_one('ul.informationshort li.date a')
                if pubDate:
                    pubDate = pubDate.attrs['href']
                    pubDate = str(pubDate).split('/')
                    if len(pubDate) == 6:
                        pubDate = (int(pubDate[-3]),int(pubDate[-2]),int(pubDate[-1]))
                        pubDate = datetime.datetime(
                            *pubDate,
                            tzinfo=tz()
                        )
                    else:
                        pubDate = now()
                else:
                    pubDate = now()
                href = nullCheck(post.select_one('a'), func = lambda x: str(x.attrs['href']))
                tags = nullCheck(post.select_one('div.tags')).replace('\n','').replace('\t','')
                links = []
                for link in post.select('div.downloadlinks a'):
                    link.string = str(link.attrs['href'])
                description = f"Tags: {tags}\nLinks:\n{"\n".join(links)}"
                description = post.prettify()
                items.append(Item(
                    title=title,
                    link=href,
                    author="Html scrape to rss",
                    guid=Guid(href),
                    pubDate=pubDate,
                    description=description
                ))
            cls.items = items
            cls.last_update = now()
        except Exception as e:
            print("Failed to update RSS", e)

class SVSComicsMuscle(SVSComics):
    title = "SVSComics - Category: Muscle Growth"
    url = "https://svscomics.com/category/muscle+growth"
    link = "https://svscomics.com/category/muscle+growth"
class SVSComicsPornComics(SVSComics):
    title = "SVSComics - Category: Porn Comics"
    url = "https://svscomics.com/porn-comics"
    link = "https://svscomics.com/porn-comics"
class SVSComics3DPornComics(SVSComics):
    title = "SVSComics - Category: 3D Porn Comics"
    url = "https://svscomics.com/3d-comics"
    link = "https://svscomics.com/3d-comics"
class SVSComicsHentaiComics(SVSComics):
    title = "SVSComics - Category: Hentai Manga & Doujinshi"
    url = "https://svscomics.com/hentai-manga-comics"
    link = "https://svscomics.com/hentai-manga-comics"