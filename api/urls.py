from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import auth, profile, movie, payment


router = DefaultRouter()
router.register("profile", profile.ProfileView)
router.register("role", profile.RoleView)
router.register("lang", movie.MovieLanguageView)
router.register("genre", movie.MovieGenreView)
router.register("submit", movie.SubmissionView)
router.register("movie", movie.MovieView)
router.register("review", movie.MovieReviewView)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", auth.AuthTokenView.as_view()),
    path("payment/verify/", payment.VerifyPayment.as_view()),
]
