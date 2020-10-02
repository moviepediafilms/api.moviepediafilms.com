from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import auth, profile


router = DefaultRouter()
router.register("profile", profile.ProfileView)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", auth.AuthTokenView.as_view()),
]
