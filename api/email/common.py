from rest_framework.authtoken.models import Token
import logging
import abc


logger = logging.getLogger("api.email")


class TemplateVariables:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @property
    def name(self):
        user = self.kwargs["user"]
        return user.get_full_name()

    @property
    def token(self):
        user = self.kwargs["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return token.key

    @property
    def profile_aware_link(self):
        """If profile is complete the link should point to notification page, otherwise to signup page"""

        user = self.kwargs["user"]
        if not user.is_active:
            # the director profile is not complete, send link to complete the profile
            return f"sign-up?token={self.token}&email={user.email}&id={user.profile.id}"
        return "notification"

    @property
    def movie_title(self):
        movie = self.kwargs["movie"]
        if movie:
            return movie.title


class TEMPLATES:
    # WELCOME = 1
    VERIFY = 2
    PASSWORD_RESET = 3
    DIRECTOR_APPROVAL = 4
    SUBMIT_CONFIRM_DIRECTOR = 5
    SUBMIT_CONFIRM_CREW = 6
    WELCOME_MDFF = 7


template_variables_map = {
    # TEMPLATES.WELCOME: ("user",),
    TEMPLATES.DIRECTOR_APPROVAL: ("profile_aware_link", "movie_title"),
    TEMPLATES.PASSWORD_RESET: ("token", "name"),
    TEMPLATES.WELCOME_MDFF: ("movie_title", "name"),
    TEMPLATES.VERIFY: ("token", "name"),
    TEMPLATES.SUBMIT_CONFIRM_DIRECTOR: ("name",),
    TEMPLATES.SUBMIT_CONFIRM_CREW: ("name",),
}


class BaseEmailBuilder:
    @abc.abstractmethod
    def build(self, user, template_id, fail_silently=False, **kwargs):
        pass
