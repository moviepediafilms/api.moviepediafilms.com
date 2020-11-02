from logging import getLogger

from django.db.models import Count
from rest_framework import permissions, viewsets, mixins, parsers
from api.serializers.movie import MovieSerializerSummary
from api.serializers.profile import (
    ProfileDetailSerializer,
    ProfileImageSerializer,
    RoleSerializer,
    FollowSerializer,
    ProfileSerializer,
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


class AudienceLeaderboardView(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    ordering = ["rank"]


class FilmmakerLeaderboardView(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    ordering = ["pop_score"]


class RoleView(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class FollowView(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.UpdateModelMixin
):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        logger.debug(f"{self.action} {str(self.request.query_params)}")
        if self.action == "list":
            # profiles that are following the logged in user
            if "followers" in self.request.query_params:
                return self.request.user.profile.followed_by.all()
            # profiles that are followed by the logged in user (yes its correct)
            return self.request.user.profile.follows.all()
        return Profile.objects.annotate(following=Count("follows"))

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileSerializer
        return FollowSerializer

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


#
# class FollowersView(viewsets.GenericViewSet, mixins.ListModelMixin):
#     serializer_class = ProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         query = self.request.user.profile.followed_by.all()
#         logger.debug(query.query)
#         return query


# class FollowingView(viewsets.GenericViewSet, mixins.ListModelMixin):
#     serializer_class = ProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return self.request.user.profile.follows.all()


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
