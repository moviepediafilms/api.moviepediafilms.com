from api.models.movie import CrewMember
from logging import getLogger

from django.db.models import Count
from rest_framework import permissions, viewsets, mixins, parsers, response
from rest_framework.decorators import action
from api.serializers.movie import MovieSerializerSummary
from api.serializers.profile import (
    ProfileDetailSerializer,
    ProfileImageSerializer,
    RoleSerializer,
    FollowSerializer,
    ProfileSerializer,
)
from api.constants import RECOMMENDATION
from api.models import Profile, Role, MovieList


logger = getLogger(__name__)


class IsOwnProfile(permissions.BasePermission):
    def has_object_permission(self, request, view, object: Profile):
        logger.debug(f"{object.user} == {request.user}")
        return object.user == request.user


class IsCreateSafeOrIsOwner(IsOwnProfile):
    def has_object_permission(self, request, view, object: Profile):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "POST":
            return True
        return super().has_object_permission(request, view, object)


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
    permission_classes = [IsCreateSafeOrIsOwner]
    filterset_fields = ["is_celeb"]
    lookup_field = "user__id"

    def get_serializer_class(self):
        if self.action == "filmography":
            return MovieSerializerSummary
        return ProfileDetailSerializer

    @action(methods=["get"], detail=True)
    def filmography(self, pk=None, **kwargs):
        profile = self.get_object()
        movies = profile.movies.distinct()
        page = self.paginate_queryset(movies)
        if page is not None:
            serializer = self.get_serializer(instance=page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(instance=movies, many=True)
        return response.Response(serializer.data)


class AudienceLeaderboardView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    ordering = ["rank"]


class FilmmakerLeaderboardView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    ordering = ["pop_score"]


class RoleView(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class FollowView(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    queryset = Profile.objects.all()
    lookup_field = "user__id"
    permission_classes = [permissions.IsAuthenticated]

    @action(methods=["get"], detail=True)
    def followers(self, pk=None, **kwargs):
        profile = self.get_object()
        # profiles that are following the logged in user
        followers = profile.followed_by.all()
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = self.get_serializer(instance=page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(instance=followers, many=True)
        return response.Response(serializer.data)

    @action(methods=["get"], detail=True)
    def following(self, pk=None, **kwargs):
        profile = self.get_object()
        # profiles that are followed by the logged in user (yes its correct)
        queryset = profile.follows.all()
        followings = self.paginate_queryset(queryset=queryset)
        page = self.paginate_queryset(followings)
        if page is not None:
            serializer = self.get_serializer(instance=page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(instance=followings, many=True)
        return response.Response(serializer.data)

    def get_queryset(self):
        return Profile.objects.annotate(following=Count("follows"))

    def get_serializer_class(self):
        if self.action in ("followers", "following"):
            return ProfileSerializer
        return FollowSerializer

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
            owner=user, name=RECOMMENDATION
        ).first()
        if recommend_list:
            return recommend_list.movies.all()
        return MovieList.objects.none()
