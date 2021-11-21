from api.models.payment import Order
from datetime import timedelta, datetime
from logging import getLogger

from django.utils.timezone import make_aware, get_current_timezone
from django.db.models import Count
from django.db import transaction


import django_filters as filters
from rest_framework import mixins, parsers, viewsets, response, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models.movie import CrewMember, MpGenre
from api.constants import MOVIE_STATE, RECOMMENDATION
from api.serializers.movie import (
    CreateOrderSerializer,
    OrderSerializer,
    SubmissionSerializer,
    MoviePosterSerializer,
    MovieLanguageSerializer,
    GenreSerializer,
    MovieSerializer,
    MovieReviewDetailSerializer,
    MovieListSerializer,
    CrewMemberRequestSerializer,
    MovieSerializerSummary,
    MpGenreSerializer,
    UpdateOrderSerializer,
)
from api.models import (
    Movie,
    MoviePoster,
    MovieLanguage,
    Genre,
    MovieRateReview,
    MovieList,
    CrewMemberRequest,
    Role,
    Contest,
    Profile,
)
from .utils import paginated_response

logger = getLogger(__name__)


class IsMovieOrderOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, object: Movie):
        return object.orders.filter(owner=request.user).exists()


class IsOrderOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, object: Order):
        return object.owner == request.user


class SubmissionView(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    queryset = Movie.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [IsMovieOrderOwner]

    @transaction.atomic
    def perform_create(self, serializer):
        logger.info(f"perform_create::{self.request.user.email}")
        serializer.save(user=self.request.user)
        logger.info("perform_create::end")

    @transaction.atomic
    def perform_update(self, serializer):
        logger.info(f"perform_update::{self.request.user.email}")
        serializer.save(user=self.request.user)
        logger.info("perform_update::end")


class OrderView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):

    permission_classes = [IsOrderOwner]
    filterset_fields = ["state", "package", "movies__id"]

    def get_queryset(self):
        return Order.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        return {
            "create": CreateOrderSerializer,
            "update": UpdateOrderSerializer,
            "partial_update": UpdateOrderSerializer,
            "list": OrderSerializer,
        }[self.action]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class MovieView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    ordering_fields = ["publish_on", "recommend_count"]
    ordering = ["-publish_on", "-recommend_count", "title"]
    filterset_fields = {
        "genres__name": ["iexact", "in"],
        "lang__name": ["iexact", "in"],
        "type": ["exact"],
    }
    search_fields = [
        "title",
        "crew__user__first_name",
        "crew__user__last_name",
    ]

    def get_queryset(self):
        base_qs = Movie.objects.filter(state=MOVIE_STATE.PUBLISHED)
        if self.action == "new_releases":
            latest_movie = (
                base_qs.exclude(publish_on__isnull=True).order_by("-publish_on").first()
            )
            if latest_movie:
                last_publish_date = latest_movie.publish_on.date()
                last_publish_date = latest_movie.publish_on.astimezone(
                    get_current_timezone()
                )
                return base_qs.filter(publish_on__date=last_publish_date)
            else:
                return Movie.objects.none()
        if self.action == "partial_update":
            return Movie.objects.filter(
                crewmember__role__name="Director",
                crewmember__profile=self.request.user.profile,
            ).distinct()
        return base_qs

    def get_serializer_class(self):
        if self.action in ("list", "new_releases"):
            return MovieSerializerSummary
        return MovieSerializer

    def get_serializer_context(self):
        return dict(request=self.request)

    @action(methods=["get"], detail=False)
    def new_releases(self, request, pk=None, **kwargs):
        """All movies released on same day - need not be today any n-1 day"""
        return paginated_response(self, self.get_queryset())


class MoviesByView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """All Movie of a director"""

    queryset = Profile.objects
    serializer_class = MovieSerializerSummary
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        director_membership = CrewMember.objects.filter(
            profile=profile, role__name="Director"
        ).all()
        movies_queryset = Movie.objects.filter(
            id__in=[dm.movie_id for dm in director_membership],
            state=MOVIE_STATE.PUBLISHED,
        )
        queryset = self.filter_queryset(movies_queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MoviePosterView(viewsets.ModelViewSet):
    queryset = MoviePoster.objects.all()
    serializer_class = MoviePosterSerializer


class MovieLanguageView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = MovieLanguage.objects.all()
    serializer_class = MovieLanguageSerializer


class GenreView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class IsMovieRateReviewOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, object: MovieRateReview):
        me = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        return object.author == me


class MovieReviewView(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsMovieRateReviewOwner]
    serializer_class = MovieReviewDetailSerializer
    filterset_fields = ["movie__id", "author__id"]
    ordering_fields = ["published_at", "number_of_likes"]
    ordering = [
        "-number_of_likes",
        "-published_at",
    ]

    def get_queryset(self):
        query = MovieRateReview.objects.annotate(number_of_likes=Count("liked_by"))
        if self.request.method in permissions.SAFE_METHODS:
            return query.exclude(content__isnull=True).exclude(content__exact="")
        else:
            return query

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MovieReviewLikeView(
    viewsets.GenericViewSet, mixins.DestroyModelMixin, mixins.UpdateModelMixin
):
    queryset = MovieRateReview.objects

    def update(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        instance.liked_by.add(user)
        instance.save()
        return response.Response(dict(success=True))

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        instance.liked_by.remove(user)
        instance.save()
        return response.Response(dict(success=True))


class MovieWatchlistView(
    mixins.DestroyModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    def get_queryset(self):
        return Movie.objects

    def update(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        user.profile.watchlist.add(movie)
        user.profile.save()
        return response.Response(dict(success=True))

    def destroy(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        user.profile.watchlist.remove(movie)
        user.profile.save()
        return response.Response(dict(success=True))


class MovieRecommendView(
    viewsets.GenericViewSet,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
):
    # TODO: make sure front-end is not using it and then delete it
    # recommendation should be done via ProfileView additional action
    ordering_fields = []
    queryset = Contest.objects.filter(state=MOVIE_STATE.PUBLISHED)

    def _is_movie_live(self, movie):
        return (
            movie.state == MOVIE_STATE.PUBLISHED
            and movie.contest
            and movie.contest.is_live()
        )

    def _add_to_contest_recommend(self, movie, user):
        if self._is_movie_live(movie):
            logger.debug("MOVIE IS LIVE")
            # fetch the list for that month
            # check the size for list
            contest_recomm_list, _ = MovieList.objects.get_or_create(
                name=movie.contest.name, owner=user, contest=movie.contest, frozen=True
            )
            if (
                contest_recomm_list.movies.count()
                >= contest_recomm_list.contest.max_recommends
            ):
                return response.Response(
                    dict(
                        success=False,
                        message=f"Cannot recommend more that {contest_recomm_list.contest.max_recommends} movies from {contest_recomm_list.contest.name}",
                    )
                )
            else:
                contest_recomm_list.movies.add(movie)
                contest_recomm_list.save()
                logger.debug("Added to contest list")

    def _remove_from_contest_recommend(self, movie, user):
        if self._is_movie_live(movie):
            logger.debug("MOVIE IS LIVE")
            contest_recomm_list = MovieList.objects.filter(
                owner=user, contest=movie.contest
            ).first()
            if contest_recomm_list and movie in contest_recomm_list.movies.all():
                contest_recomm_list.movies.remove(movie)
                contest_recomm_list.save()
                logger.debug("Removed from contest list")

    def update(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        recommendation_list, _ = MovieList.objects.get_or_create(
            owner=user, name=RECOMMENDATION
        )
        logger.debug(f"{recommendation_list}")
        if movie in recommendation_list.movies.all():
            return response.Response(dict(success=False))
        self._add_to_contest_recommend(movie, user)
        recommendation_list.movies.add(movie)
        recommendation_list.save()
        movie.recommend_count += 1
        movie.save()
        return response.Response(dict(success=True))

    def destroy(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        recommendation_list = MovieList.objects.get(owner=user, name=RECOMMENDATION)
        if recommendation_list:
            if movie in recommendation_list.movies.all():
                recommendation_list.movies.remove(movie)
                recommendation_list.save()
                movie.recommend_count -= 1
                movie.save()
                self._remove_from_contest_recommend(movie, user)
            else:
                return response.Response(dict(success=False))
        return response.Response(dict(success=True))


class IsMovieListOwnerOrLike(permissions.BasePermission):
    def has_object_permission(self, request, view, object: MovieList):
        me = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        return view.action == "like" or object.owner == me


class MovieListFilter(filters.FilterSet):
    contest__isnull = filters.BooleanFilter(
        field_name="contest", lookup_expr="isnull", label="Contest is null"
    )

    class Meta:
        model = MovieList
        fields = ["contest__isnull", "owner__id", "name"]


class MovieListView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsMovieListOwnerOrLike]
    queryset = MovieList.objects.annotate(
        likes=Count("liked_by"), number_of_movies=Count("movies")
    )
    filter_class = MovieListFilter
    ordering_fields = ["movies", "likes"]

    def get_serializer_class(self):
        if self.action in ("movies", "like"):
            return MovieSerializerSummary
        return MovieListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=["get"], detail=True)
    def movies(self, request, pk=None, **kwargs):
        movie_list = self.get_object()
        qs = movie_list.movies.all()
        month = request.GET.get("month")
        year = request.GET.get("year")
        if month and year:
            month = int(month)
            year = int(year)
            start = make_aware(datetime.strptime(f"{year}-{month}", "%Y-%m"))
            end = make_aware(
                datetime.strptime(f"{year}-{month+1}", "%Y-%m") - timedelta(days=1)
            )
            qs = qs.filter(publish_on__gte=start, publish_on__lte=end)
        return paginated_response(self, queryset=qs)

    @action(methods=["post", "delete"], detail=True)
    def like(self, request, pk=None, **kwargs):
        movie_list = self.get_object()
        if request.method.lower() == "post":
            movie_list.liked_by.add(request.user)
            movie_list.save()
        else:
            movie_list.liked_by.remove(request.user)
            movie_list.save()
        return response.Response(
            {"success": True, "like_count": movie_list.liked_by.count()}
        )


class IsDirectorCreatorOrRequestor(permissions.BasePermission):
    def has_object_permission(self, request, view, object: CrewMemberRequest):
        me = request.user
        if request.method in permissions.SAFE_METHODS:
            return (
                object.user == me
                or object.requestor == me
                or object.movie.crewmember_set.filter(
                    role__name="Director", profile__user=me
                ).exists()
            )

        director = Role.objects.get(name="Director")
        return Movie.objects.filter(
            id=object.movie.id,
            crewmember__role=director,
            crewmember__profile=me.profile,
        ).exists()


class CrewMemberRequestView(viewsets.ModelViewSet):
    # either you are director or you are a crew member
    permission_classes = [permissions.IsAuthenticated, IsDirectorCreatorOrRequestor]
    serializer_class = CrewMemberRequestSerializer
    filterset_fields = ["requestor__id"]

    def get_queryset(self):
        return CrewMemberRequest.objects

    def perform_create(self, serializer):
        serializer.save(logged_in_user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(logged_in_user=self.request.user)


class MpGenreView(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = MpGenre.objects.filter(live=True)

    def get_serializer_class(self):
        return {"movies": MovieSerializerSummary}.get(self.action, MpGenreSerializer)

    @action(methods=["get"], detail=True)
    def movies(self, request, **kwargs):
        mp_genre = self.get_object()
        movies_qs = mp_genre.movies.order_by(
            "-publish_on", "-recommend_count", "title"
        ).all()
        return paginated_response(self, movies_qs)
