from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import auth, profile, movie, payment


router = DefaultRouter()
router.register("profile", profile.ProfileView, basename="profile")
router.register("profile-image", profile.ProfileImageView, basename="profileimage")
router.register("role", profile.RoleView, basename="role")
router.register("follow", profile.FollowView, basename="follow")
router.register("lang", movie.MovieLanguageView, basename="lang")
router.register("genre", movie.MovieGenreView, basename="genre")
router.register("submit", movie.SubmissionView, basename="submit")
router.register("movie", movie.MovieView, basename="movie")
router.register("review", movie.MovieReviewView, basename="review")
router.register("review-like", movie.MovieReviewLikeView, basename="reviewlike")
router.register("watchlist", movie.MovieWatchlistView, basename="watchlist")
router.register("recommend", movie.MovieRecommendView, basename="recommen")
router.register("movie-list", movie.MovieListView, basename="movielist")
router.register(
    "crew-member-request", movie.CrewMemberRequestView, basename="crewmemberrequest"
)
router.register("my-watchlist", profile.MyWatchlistView, basename="mywatchlist")
router.register("my-recommends", profile.MyRecommendedView, basename="myrecommends")
router.register(
    "audience-leaderboard",
    profile.AudienceLeaderboardView,
    basename="audienceleaderboard",
)
router.register(
    "filmmaker-leaderboard",
    profile.FilmmakerLeaderboardView,
    basename="filmmakerleaderboard",
)


urlpatterns = [
    path("", include(router.urls)),
    path("auth/", auth.AuthTokenView.as_view()),
    path("payment/verify/", payment.VerifyPayment.as_view()),
]
