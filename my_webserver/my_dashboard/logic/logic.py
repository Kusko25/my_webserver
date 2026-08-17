import logging
import re
from collections import defaultdict
from datetime import date, datetime

import feedparser as fp
import requests
from bs4 import BeautifulSoup
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from ..models import (
    AppSettings,
    Movie,
    MovieInstance,
    TVShow,
    TVShowEpisode,
    TVShowEpisodeInstance,
)
from ..utils import process_show_name

logger = logging.getLogger(__name__)


def get_tv_schedule(ep_date: date):
    schedule = TVShowEpisode.objects.filter(air_date=ep_date)
    if len(schedule) > 0:
        return schedule
    else:  # Assume data hasn't been fetched yet
        response = requests.get(
            f"https://www.pogdesign.co.uk/cat/{ep_date.month}-{ep_date.year}"
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error fetching TV schedule for {ep_date}: {e}")
            return None

        new_episodes = list()
        soup = BeautifulSoup(response.content, features="html.parser")
        try:  # So many ways to raise exceptions when parsing soup
            for i, day in enumerate(
                soup.find_all(class_=lambda c: c and (c == "day" or c == "today")) # type: ignore
            ):
                for episode in day.find_all(
                    class_=lambda c: c and ("ep" in c and "info" in c)
                ):
                    show_name = episode.a
                    episode_str = show_name.find_next_sibling("a")
                    episode_id = episode.label.attrs["for"]
                    episode_name = (
                        BeautifulSoup(
                            requests.get(
                                f"https://www.pogdesign.co.uk/cat/q/{episode_id}"
                            ).content,
                            features="html.parser",
                        )
                        .find("div", id="popheader")
                        .strong.get_text("\n")
                        .split("\n")[1]
                    )
                    show_name = show_name.text
                    episode_str = episode_str.text
                    season, episode, switch = "", "", -1
                    for c in episode_str:
                        if switch == -1 and c == "s":
                            switch = 0
                        elif switch == 0 and c.isdigit():
                            season += c
                        elif switch == 0 and c == "e":
                            switch = 1
                        elif switch == 1 and c.isdigit():
                            episode += c
                        else:
                            raise Exception(
                                f"Unexpected character {c} in {episode_str}"
                            )
                    season, episode = int(season), int(episode)
                    new_episodes.append(
                        {
                            "title": episode_name,
                            "season": season,
                            "episode": episode,
                            "air_date": date(
                                day=i + 1, month=ep_date.month, year=ep_date.year
                            ),
                            "tv_show": show_name,
                            "save": False,
                        }
                    )
        except Exception as e:
            logger.error(f"Error parsing HTML for TV schedule: {e}")
            raise e
            return None

        tv_shows_db = TVShow.objects.all()
        tv_shows_query = {
            process_show_name(episode["tv_show"]) for episode in new_episodes
        }
        tv_shows = {show.title for show in tv_shows_db}
        new_tv_shows = tv_shows_query - tv_shows
        try:
            with transaction.atomic():
                for show in new_tv_shows:
                    TVShow(title=show).save()
        except Exception as e:
            logger.error(f"Error saving new TV shows to database: {e}")
            return None

        logger.info(f"New TV shows: {new_tv_shows}")

        tv_shows_db = {show.title: show for show in TVShow.objects.all()}

        for episode in new_episodes:
            episode["tv_show"] = tv_shows_db[process_show_name(episode["tv_show"])]

        new_episodes = [TVShowEpisode.make_new(**episode) for episode in new_episodes]

        # Save new episodes in bulk, rollback if any fail
        try:
            with transaction.atomic():
                for episode in new_episodes:
                    episode.save()
        except Exception as e:
            logger.error(f"Error saving new episodes to database: {e}")
            return None

        schedule = TVShowEpisode.objects.filter(air_date=date)
        return schedule


def parse_movie_feed():
    url = AppSettings.get_key("movies_feed_url")
    if (
        AppSettings.get_key("movies_last_update")
        + timezone.timedelta(hours=AppSettings.get_key("movies_update_interval"))
        > timezone.now()
    ):
        return False
    feed = fp.parse(url)
    if feed["bozo"]:
        logger.error(f"Error parsing feed: {feed.bozo_exception}")
        return False
    entries = feed.entries
    filters = AppSettings.get_key("movies_filters")
    movie_dict = defaultdict(list)
    for entry in entries:
        year, resolution, group, movie_name = "","","",""
        try:
            title = str(entry["title"])
            # Replace all whitespace with a dot
            title = re.sub(r"\s", ".", title)
            # Isolate movie name, detected by capturing everything before the year
            movie_name = re.search(r"(.*?)[\.]\d{4}.", title).group(1)
            movie_name = movie_name.replace(".", " ").title()
            # Replace all non-alphanumeric characters with a space
            movie_name = re.sub(r"\W", " ", movie_name)
            title = title[len(movie_name) + 1 :]  # cut off movie name
            year = title.split(".", 1)[0]  # seems to be the end of any clear pattern
            title = title[len(year) + 1 :]  # cut off year
            resolution = re.search(r"\d{3,4}p", title)
            if resolution:
                resolution = resolution.group(0)
            else:
                resolution = "Unknown"
            title = title[len(resolution) + 1 :]  # cut off resolution
            # Isolate group, last element seperated by a dash
            if len(title.split("-")) > 1:
                group = title.split("-")[-1]
            else:
                group = "Unknown"
            cam = any(filter in title for filter in filters)
            movie_name = process_show_name(movie_name)
            new_object = {
                "year": int(year),
                "resolution": resolution,
                "group": group,
                "movie_name": movie_name,
                "link": entry["link"],
                "entry_time": entry["published_parsed"],
            }
            assert (
                new_object["year"] > 1900 and new_object["year"] < 2100
            ), "Year out of range"
            assert (
                len(new_object["resolution"]) > 0 and len(new_object["resolution"]) < 10
            ), "Presumably invalid resolution"
            assert len(new_object["group"]) > 0, "Presumably invalid group"
            assert len(new_object["movie_name"]) > 0, "Presumably invalid movie name"
            assert "http" in new_object["link"], "Presumably invalid link"
            movie_dict[new_object["movie_name"]].append(new_object)
        except Exception as _:
            logger.error(
                f'Error parsing movie feed entry: {year} {resolution} {group} {movie_name} {entry["link"]}'
            )
            continue  # skip if any of the above fails. Regex is not to be trusted
        if cam:
            continue

    movies_db = Movie.objects.all()
    movies_db = {movie.title: movie for movie in movies_db}
    try:
        with transaction.atomic():
            for movie in movie_dict:
                if movie not in movies_db:
                    movies_db[movie] = Movie(
                        title=movie, release_year=movie_dict[movie][0]["year"]
                    )
                    movies_db[movie].save()
    except Exception as e:
        logger.error(f"Error saving new movies to database: {e}")
        return e

    existing_instances = []
    for movie in movie_dict:
        existing_instances.extend(MovieInstance.objects.filter(movie=movies_db[movie]))
    existing_instances = {
        (instance.resolution, instance.group, instance.url)
        for instance in existing_instances
    }
    for movie in list(movie_dict.keys()):
        movie_dict[movie] = [
            MovieInstance(
                movie=movies_db[movie],
                resolution=instance["resolution"],
                group=instance["group"],
                url=instance["link"],
                date_added=date(
                    instance["entry_time"].tm_year,
                    instance["entry_time"].tm_mon,
                    instance["entry_time"].tm_mday,
                ),
            )
            for instance in movie_dict[movie]
            if (instance["resolution"], instance["group"], instance["link"])
            not in existing_instances
        ]
        if len(movie_dict[movie]) == 0:
            del movie_dict[movie]
    try:
        with transaction.atomic():
            for movie in movie_dict:
                for instance in movie_dict[movie]:
                    instance.save()
    except Exception as e:
        logger.error(f"Error saving new movie instances to database: {e}")
        return e
    AppSettings.set_key("movies_last_update", timezone.now())
    return True


def parse_tv_feed(request):
    url = AppSettings.get_key("tv_feed_url")
    if timezone.now() - AppSettings.get_key("tvshows_last_update") < timezone.timedelta(
        hours=AppSettings.get_key("tvshows_update_interval")
    ):
        return False, InterruptedError("Update interval not reached")
    feed = fp.parse(url)
    if feed["bozo"]:
        logger.error(f"Error parsing feed: {feed.bozo_exception}")
        messages.error(request, f"Error parsing feed: {feed.bozo_exception}")
        return False, feed.bozo_exception
    filters = AppSettings.get_key("tv_filters")
    show_dict = defaultdict(lambda: defaultdict(list))
    for entry in feed.entries:
        show, season, episode, resolution, source, group, _ = (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        elements = entry.title.split(" & ")
        for element in elements:
            title = element
            re_match = re.match(
                r"(.*?)[Ss](\d{2})[Ee](\d{2}).*?(\d{3,4}p)\.(.*?)\..*?-(.*)", title
            )
            if not re_match:
                continue
            show, season, episode, resolution, source, group = re_match.groups()
            show = show.replace(".", " ").strip()
            show = process_show_name(show)
            new_object = {
                "resolution": resolution,
                "source": source,
                "group": group,
                "show_name": show,
                "link": entry["link"],
                "entry_time": entry["published"],
                "season": int(season),
                "episode": int(episode),
            }
            if any(filter in title for filter in filters):
                continue
            try:
                assert (
                    len(new_object["resolution"]) > 0
                    and len(new_object["resolution"]) < 10
                ), "Presumably invalid resolution"
                assert len(new_object["group"]) > 0, "Presumably invalid group"
                assert len(new_object["show_name"]) > 0, "Presumably invalid movie name"
                assert "http" in new_object["link"], "Presumably invalid link"
            except Exception as _:
                logger.error(
                    f'Error parsing tv feed entry: {show} {season} {episode} {resolution} {group} {entry["link"]}'
                )
                messages.warning(
                    request,
                    f'Error parsing tv feed entry: {show} {season} {episode} {resolution} {group} {entry["link"]}',
                )
                continue  # skip if any of the above fails. Regex is not to be trusted
            show_dict[new_object["show_name"]][
                (new_object["season"], new_object["episode"])
            ].append(new_object)

    shows_db = TVShow.objects.all()
    shows_db = {show.title: show for show in shows_db}
    try:
        with transaction.atomic():
            shows = []
            for show in show_dict:
                if show not in shows_db:
                    shows.append(TVShow(title=show))
                    shows_db[show] = shows[-1]
            TVShow.objects.bulk_create(shows)
    except Exception as e:
        logger.error(f"Error saving new shows to database: {e}")
        messages.error(request, f"Error saving new shows to database: {e}")
        return False, e

    new_episodes = []
    # title = models.CharField(max_length=200)
    # season = models.IntegerField()
    # episode = models.IntegerField()
    # air_date = models.DateField(blank=True, null=True)
    # description = models.TextField(blank=True, null=True)
    # tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE)
    for show in show_dict:
        show_episodes = TVShowEpisode.objects.filter(tv_show=shows_db[show])
        show_episodes = {
            (episode.season, episode.episode): episode for episode in show_episodes
        }
        for season, episode in show_dict[show]:
            if (season, episode) in show_episodes:
                continue
            show_episode = TVShowEpisode(
                title=f"S{season:02d}E{episode:02d}",
                season=season,
                episode=episode,
                air_date=date.today(),
                tv_show=shows_db[show],
            )
            new_episodes.append(show_episode)
    try:
        with transaction.atomic():
            TVShowEpisode.objects.bulk_create(new_episodes)
    except Exception as e:
        logger.error(f"Error saving new show episodes to database: {e}")
        messages.error(request, f"Error saving new show episodes to database: {e}")
        return False, e

    # episode = models.ForeignKey(TVShowEpisode, on_delete=models.CASCADE)
    # resolution = models.CharField(max_length=50, default='Unknown')
    # source = models.CharField(max_length=50, default='Unknown')
    # group = models.CharField(max_length=50, default='Unknown')
    # url = models.URLField(max_length=200)
    # date_added = models.DateField(auto_now_add=True)

    new_instances = []
    for show in show_dict:
        show_episodes = TVShowEpisode.objects.filter(tv_show=shows_db[show])
        show_episodes = {
            (episode.season, episode.episode): episode for episode in show_episodes
        }
        for season, episode in show_dict[show]:
            existing_instances = TVShowEpisodeInstance.objects.filter(
                episode=show_episodes[(season, episode)]
            )
            existing_instances = {
                (instance.resolution, instance.source, instance.group, instance.url)
                for instance in existing_instances
            }
            for instance in show_dict[show][(season, episode)]:
                if (
                    instance["resolution"],
                    instance["source"],
                    instance["group"],
                    instance["link"],
                ) in existing_instances:
                    continue
                new_instance = TVShowEpisodeInstance(
                    episode=show_episodes[(season, episode)],
                    resolution=instance["resolution"],
                    source=instance["source"],
                    group=instance["group"],
                    url=instance["link"],
                    time_posted=datetime.strptime(
                        instance["entry_time"], "%a, %d %b %Y %H:%M:%S %z"
                    ),
                )
                new_instances.append(new_instance)
    try:
        with transaction.atomic():
            TVShowEpisodeInstance.objects.bulk_create(new_instances)
    except Exception as e:
        logger.error(f"Error saving new show instances to database: {e}")
        messages.error(request, f"Error saving new show instances to database: {e}")
        return False, e

    AppSettings.set_key("tvshows_last_update", timezone.now())
    return True, None
