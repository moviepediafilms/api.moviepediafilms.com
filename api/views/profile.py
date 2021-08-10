from api.models.movie import Movie, TopCreator
from logging import getLogger

from django.db.models import Count, Q
from rest_framework import permissions, viewsets, mixins, parsers, response
from rest_framework.decorators import action
from api.serializers.movie import (
    CrewMemberRequestSerializer,
    MovieSerializerSummary,
    SubmissionEntrySerializer,
    MovieRecommendSerializer,
)
from api.serializers.profile import (
    ProfileDetailSerializer,
    ProfileImageSerializer,
    RoleSerializer,
    FollowSerializer,
    ProfileSerializer,
    NotificationSerializer,
)
from api.constants import CREW_MEMBER_REQUEST_STATE, RECOMMENDATION, MOVIE_STATE
from api.models import Profile, Role, MovieList, CrewMemberRequest


logger = getLogger(__name__)


class IsOwnProfile(permissions.BasePermission):
    def has_object_permission(self, request, view, object: Profile):
        return object.user == request.user


class IsCreateSafeOrIsOwner(IsOwnProfile):
    def has_object_permission(self, request, view, object: Profile):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method in ("POST", "PATCH"):
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
    search_fields = ["user__first_name", "user__last_name"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("is_celeb"):
            return qs.order_by("-celeb_order")
        return qs

    def get_serializer_class(self):
        if self.action in ("filmography", "movie_approvals"):
            return MovieSerializerSummary
        if self.action in ("submissions"):
            return SubmissionEntrySerializer
        if self.action == "notifications":
            return NotificationSerializer
        if self.action == "crew_approvals":
            return CrewMemberRequestSerializer
        if self.action == "recommends":
            if self.request.method in ("POST", "DELETE"):
                return MovieRecommendSerializer
            else:
                return MovieSerializerSummary
        return ProfileDetailSerializer

    @action(methods=["get"], detail=True)
    def filmography(self, pk=None, **kwargs):
        profile = self.get_object()
        queryset = profile.movies
        is_private_view = self.request.user == profile.user
        if is_private_view:
            queryset = queryset.filter(
                Q(state=MOVIE_STATE.PUBLISHED)
                | (Q(crewmember__role__name="Director") & Q(approved=True))
            )
        else:
            queryset = queryset.filter(state=MOVIE_STATE.PUBLISHED)
        movies = queryset.distinct()
        return self._build_paginated_response(movies)

    @action(methods=["get"], detail=True, permission_classes=[IsOwnProfile])
    def submissions(self, pk=None, **kwargs):
        profile = self.get_object()
        if self.request.user != profile.user:
            return response.Response(
                {"error": "You are not authorized to view this page"}, 403
            )
        orders = profile.user.orders.all().prefetch_related("movies")
        movies = {}
        for order in orders:
            movies.update({m.id: m for m in order.movies.all()})
        return self._build_paginated_response(list(movies.values()))

    @action(methods=["get"], detail=True, permission_classes=[IsOwnProfile])
    def notifications(self, pk=None, **kwargs):
        profile = self.get_object()
        notifications = profile.notifications.all()
        return self._build_paginated_response(notifications)

    @action(
        methods=["get"],
        detail=True,
        permission_classes=[IsOwnProfile],
        url_path="movie-approvals",
    )
    def movie_approvals(self, pk=None, **kwargs):
        profile = self.get_object()
        movies = profile.movies.filter(
            crewmember__role__name="Director", approved__isnull=True
        ).all()
        return self._build_paginated_response(movies)

    @action(
        methods=["get"],
        detail=True,
        permission_classes=[IsOwnProfile],
        url_path="crew-approvals",
    )
    def crew_approvals(self, pk=None, **kwargs):
        profile = self.get_object()
        my_movies = profile.movies.filter(crewmember__role__name="Director").all()
        crew_requests = CrewMemberRequest.objects.filter(
            movie__in=my_movies, state=CREW_MEMBER_REQUEST_STATE.SUBMITTED
        ).all()
        return self._build_paginated_response(crew_requests)

    @action(methods=["get", "post", "delete"], detail=True)
    def recommends(self, pk=None, **kwargs):
        """
        manages user's personal recommendations list.
        POST and DELETE methods are used to add movies where as GET
        is used to fetch all the movies in personal recommend list
        """

        profile = self.get_object()
        movie_list = MovieList.objects.filter(
            owner=profile.user, name=RECOMMENDATION
        ).first()
        if self.request.method == "GET":
            movies = Movie.objects.none()
            if movie_list:
                movies = movie_list.movies.all()
            logger.debug(f"{pk} {profile} {movies}")
            return self._build_paginated_response(movies)
        elif self.request.method in ("POST", "DELETE"):
            # FIXME: handle allow modification to self profile only via permission classes
            profile = self.request.user.profile
            serializer = self.get_serializer(
                instance=profile,
                data=self.request.data,
                context={"request": self.request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(
                action={"POST": "add", "DELETE": "remove"}[self.request.method]
            )
            return response.Response(serializer.data)

    def _build_paginated_response(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(instance=page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(instance=queryset, many=True)
        return response.Response(serializer.data)


class AudienceLeaderboardView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Profile.objects.filter(
        is_celeb=False, curator_rank__gte=0, onboarded=True
    )
    serializer_class = ProfileSerializer
    ordering = ["curator_rank"]


class FilmmakerLeaderboardView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Profile.objects.filter(
        is_celeb=False, creator_rank__gte=0, onboarded=True
    )
    serializer_class = ProfileSerializer
    ordering = ["creator_rank"]


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
