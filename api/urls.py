from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import auth


router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", auth.AuthTokenView.as_view()),
]
