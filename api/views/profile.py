from logging import getLogger

from django.db.models import Count
from rest_framework import permissions, viewsets, mixins, parsers
from api.serializers.movie import MovieSerializerSummary
from api.serializers.profile import (
    ProfileDetailSerializer,
    ProfileImageSerializer,
    RoleSerializer,
    FollowSerializer,
)
from api.models import Profile, Role, MovieList


logger = getLogger("app.view")


class IsOwnProfile(permissions.BasePermission):
    def has_object_permission(self, request, view, object: Profile):
        return object.user == request.user


class ReadOnlyMixin:
    def has_object_permission(self, request, view, object):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_object_permission(request, view, object)


class IsOwnProfileOrReadOnly(ReadOnlyMixin, IsOwnProfile):
    pass


class ProfileImageView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnProfile]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    queryset = Profile.objects.all()
    serializer_class = ProfileImageSerializer

    def perform_update(self, serializer):
        logger.info(f"perform_image_update::{self.request.user.email}")
        serializer.save(user=self.request.user)
        logger.info("perform_image_update::end")


class ProfileView(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileDetailSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny, IsOwnProfileOrReadOnly]
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
        if recommend_list:
            return recommend_list.movies.all()
        return MovieList.objects.none()
