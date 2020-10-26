from logging import getLogger

from django.db.models import Count
from rest_framework import permissions, viewsets, mixins
from api.serializers.movie import MovieSerializerSummary
from api.serializers.profile import (
    ProfileDetailSerializer,
    RoleSerializer,
    FollowSerializer,
)
from api.models import Profile, Role, MovieList


logger = getLogger("app.view")


class ProfileView(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileDetailSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    lookup_field = "user__id"


class RoleView(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class FollowView(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    queryset = Profile.objects.annotate(following=Count("follows"))
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class MyWatchlistView(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MovieSerializerSummary

    def get_queryset(self):
        user = self.request.user
        return user.profile.watchlist.all()


class MyRecommendedView(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MovieSerializerSummary

    def get_queryset(self):
        user = self.request.user
        recommend_list = MovieList.objects.filter(
            owner=user, name="Recommendation"
        ).first()
        return recommend_list.movies.all()
