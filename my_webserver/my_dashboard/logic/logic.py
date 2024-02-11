from django.db import transaction

from ..models import TVShow, TVShowEpisode, AppSettings, Movie, MovieInstance
from ..utils import process_show_name

from datetime import date
from collections import defaultdict
import requests, logging, re
import feedparser as fp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def get_tv_schedule(ep_date: date):
    schedule = TVShowEpisode.objects.filter(air_date=ep_date)
    if len(schedule)>0:
        return schedule
    else: # Assume data hasn't been fetched yet
        response = requests.get(f'https://www.pogdesign.co.uk/cat/{ep_date.month}-{ep_date.year}')
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f'Error fetching TV schedule for {ep_date}: {e}')
            return None
        
        new_episodes = list()
        soup = BeautifulSoup(response.content,features="html.parser")
        try: # So many ways to raise exceptions when parsing soup
            for i,day in enumerate(soup.find_all(class_=lambda c: c and (c == "day" or c == "today"))):
                for episode in day.find_all(class_=lambda c: c and ("ep" in c and "info" in c)):
                    show_name = episode.a
                    episode_str = show_name.find_next_sibling("a")
                    episode_id = episode.label.attrs["for"]
                    episode_name = (BeautifulSoup(
                        requests.get(f"https://www.pogdesign.co.uk/cat/q/{episode_id}").content,
                        features="html.parser"
                        )
                        .find("div",id="popheader")
                        .strong.get_text("\n")
                        .split("\n")[1]
                    )
                    show_name = show_name.text
                    episode_str = episode_str.text
                    season, episode,switch = '', '', -1
                    for c in episode_str:
                        if switch==-1 and c =='s':
                            switch = 0
                        elif switch==0 and c.isdigit():
                            season += c
                        elif switch==0 and c=='e':
                            switch = 1
                        elif switch==1 and c.isdigit():
                            episode += c
                        else:
                            raise Exception(f'Unexpected character {c} in {episode_str}')
                    season, episode = int(season), int(episode)
                    new_episodes.append({
                        'title':episode_name,
                        'season':season,
                        'episode':episode,
                        'air_date':date(day=i+1,month=ep_date.month,year=ep_date.year),
                        'tv_show':show_name,
                        'save':False
                    })
        except Exception as e:
            logger.error(f'Error parsing HTML for TV schedule: {e}')
            raise e
            return None
        
        tv_shows_db = TVShow.objects.all()
        tv_shows_query = {process_show_name(episode['tv_show']) for episode in new_episodes}
        tv_shows = {show.title for show in tv_shows_db}
        new_tv_shows = tv_shows_query - tv_shows
        try:
            with transaction.atomic():
                for show in new_tv_shows:
                    TVShow(title=show).save()
        except Exception as e:
            logger.error(f'Error saving new TV shows to database: {e}')
            return None
        
        logger.info(f'New TV shows: {new_tv_shows}')

        tv_shows_db = {show.title:show for show in TVShow.objects.all()}

        for episode in new_episodes:
            episode['tv_show'] = tv_shows_db[process_show_name(episode['tv_show'])]

        new_episodes = [TVShowEpisode.make_new(**episode) for episode in new_episodes]
        
        # Save new episodes in bulk, rollback if any fail
        try:
            with transaction.atomic():
                for episode in new_episodes:
                    episode.save()
        except Exception as e:
            logger.error(f'Error saving new episodes to database: {e}')
            return None
        
        schedule = TVShowEpisode.objects.filter(air_date=date)
        return schedule

def parse_movie_feed():
    url = AppSettings.get_key('movies_feed_url')
    if AppSettings.get_key('movies_last_update')==date.today():
        return False
    feed = fp.parse(url)
    if feed['bozo']:
        logger.error(f'Error parsing feed: {feed.bozo_exception}')
        return False
    entries = feed.entries
    filters = AppSettings.get_key('movies_filters')
    movie_dict = defaultdict(list)
    for entry in entries:
            try:
                title = entry["title"]
                # Replace all whitespace with a dot
                title = re.sub(r"\s",".",title)
                # Isolate movie name, detected by capturing everything before the year
                movie_name = re.search(r"(.*?)[\.]\d{4}.",title).group(1)
                movie_name = movie_name.replace("."," ").title()
                # Replace all non-alphanumeric characters with a space
                movie_name = re.sub(r"\W"," ",movie_name)
                title = title[len(movie_name)+1:] # cut off movie name
                year = title.split(".",1)[0] # seems to be the end of any clear pattern
                title = title[len(year)+1:] # cut off year
                resolution = re.search(r"\d{3,4}p",title)
                if resolution:
                    resolution = resolution.group(0)
                else:
                    resolution = "Unknown"
                title = title[len(resolution)+1:] # cut off resolution
                # Isolate group, last element seperated by a dash
                if len(title.split("-"))>1:
                    group = title.split("-")[-1]
                else:
                    group = "Unknown"
                cam = any(filter in title for filter in filters)
            except:
                continue # skip if any of the above fails. Regex is not to be trusted
            if cam:
                continue
            movie_name = process_show_name(movie_name)
            movie_dict[movie_name].append({
                "year":int(year),
                "resolution":resolution,
                "group":group,
                'movie_name':movie_name,
                'link':entry['link'],
                'entry_time':entry['published_parsed']
            })

    movies_db = Movie.objects.all()
    movies_db = {movie.title:movie for movie in movies_db}
    try:
        with transaction.atomic():
            for movie in movie_dict:
                if movie not in movies_db:
                    movies_db[movie] = Movie(title=movie,release_year=movie_dict[movie][0]['year'])
                    movies_db[movie].save()
    except Exception as e:
        logger.error(f'Error saving new movies to database: {e}')
        return e
    
    for movie in movie_dict:
        movie_dict[movie] = [MovieInstance(
            movie=movies_db[movie],
            resolution=instance['resolution'],
            group=instance['group'],
            url=instance['link'],
            date_added=date(
                instance['entry_time'].tm_year,
                instance['entry_time'].tm_mon,
                instance['entry_time'].tm_mday)
        ) for instance in movie_dict[movie]]
    try:
        with transaction.atomic():
            for movie in movie_dict:
                for instance in movie_dict[movie]:
                    instance.save()
    except Exception as e:
        logger.error(f'Error saving new movie instances to database: {e}')
        return e
    AppSettings.set_key('movies_last_update',date.today())
    return True
