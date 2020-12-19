import re
import requests
from logging import getLogger

from django.core.management.base import BaseCommand
from api.models import Profile, User
from api.constants import GENDER


logger = getLogger(__name__)

DEFAULT_URL = "https://gist.githubusercontent.com/moviepedia/dc1349e485879fb53e91710be3e9fe3d/raw/celebrities.json"


class Command(BaseCommand):
    def fetch_url(self, url):
        try:
            res = requests.get(url)
        except Exception as ex:
            logger.error(f"failed to fetch the contents from {url}")
            logger.exception(ex)
            return
        else:
            try:
                celebrities = res.json()
            except Exception as ex:
                logger.error(f"The response from {url} was not in JSON format")
                logger.exception(ex)
            else:
                return celebrities

    def create_username(self, name):
        name_segs = re.split(r"\s+", name.strip())
        if len(name_segs) == 0:
            return

        username = name_segs[0].lower()
        number = ""
        while User.objects.filter(username=username + number).exists():
            number = int(number) + 1 if number else "1"
        return username + number

    def get_first_last_name(self, name):
        name_segs = re.split(r"\s+", name.strip().title())
        first_name, last_name = "", ""
        if len(name_segs) == 0:
            return "", ""
        elif len(name_segs) == 1:
            first_name = name_segs[0]
        elif len(name_segs) > 1:
            first_name = " ".join(name_segs[:-1])
            last_name = name_segs[-1]
        return first_name, last_name

    def handle(self, *args, **options):
        url = options.get("URL", DEFAULT_URL)
        celebrities = self.fetch_url(url)
        if not celebrities:
            logger.error("No celebrities were found! quitting now.")
            return
        for celeb in celebrities:
            username = self.create_username(celeb.get("name", ""))
            first_name, last_name = self.get_first_last_name(celeb.get("name", ""))
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_active=False,
            )
            title = celeb.get("title", "")
            about = celeb.get("about", "")
            about = about if not title else f"{title}\n{about}"
            gender = celeb.get("gender")
            if gender:
                gender = gender.upper()[0]
                if gender not in [GENDER.MALE, GENDER.FEMALE, GENDER.OTHERS]:
                    gender = GENDER.OTHERS
            Profile.objects.create(
                user=user,
                about=about,
                image=celeb.get("image", ""),
                gender=gender,
                is_celeb=True,
                onboarded=False,
            )
