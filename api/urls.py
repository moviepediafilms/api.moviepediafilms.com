from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import auth, profile, movie


router = DefaultRouter()
router.register("profile", profile.ProfileView)
router.register("lang", movie.MovieLanguageView)
router.register("genre", movie.MovieGenreView)


urlpatterns = [
    path("", include(router.urls)),
    path("submit/", movie.SubmissionView.as_view()),
    path("auth/", auth.AuthTokenView.as_view()),
]
