from logging import getLogger

from django.db.models import Count
from django.utils import timezone

from rest_framework import mixins, exceptions, parsers, viewsets, response, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from api.constants import MOVIE_STATE, RECOMMENDATION
from api.serializers.movie import (
    SubmissionSerializer,
    MoviePosterSerializer,
    MovieLanguageSerializer,
    MovieGenreSerializer,
    MovieSerializer,
    MovieReviewDetailSerializer,
    MovieListSerializer,
    CrewMemberRequestSerializer,
    MovieListDetailSerializer,
    MovieSerializerSummary,
    TopCreatorSerializer,
    TopCuratorSerializer,
)
from api.models import (
    User,
    Movie,
    MoviePoster,
    MovieLanguage,
    MovieGenre,
    MovieRateReview,
    MovieList,
    CrewMemberRequest,
    Role,
    Contest,
)


logger = getLogger(__name__)


class SubmissionView(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet,
):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    queryset = Movie.objects.all()
    serializer_class = SubmissionSerializer

    def perform_create(self, serializer):
        logger.info(f"perform_create::{self.request.user.email}")
        serializer.save(user=self.request.user)
        logger.info("perform_create::end")

    def perform_update(self, serializer):
        logger.info(f"perform_update::{self.request.user.email}")
        serializer.save(user=self.request.user)
        logger.info("perform_update::end")


class MovieView(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
):
    queryset = Movie.objects.filter(state=MOVIE_STATE.PUBLISHED)

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSerializerSummary
        return MovieSerializer

    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as ex:
            logger.exception(ex)
            raise exceptions.ParseError(dict(error=str(ex)))


class MoviePosterView(viewsets.ModelViewSet):
    queryset = MoviePoster.objects.all()
    serializer_class = MoviePosterSerializer


class MovieLanguageView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = MovieLanguage.objects.all()
    serializer_class = MovieLanguageSerializer


class MovieGenreView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = MovieGenre.objects.all()
    serializer_class = MovieGenreSerializer


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
    viewsets.GenericViewSet, mixins.DestroyModelMixin, mixins.UpdateModelMixin,
):
    serializer = MovieSerializerSummary

    def get_queryset(self):
        if self.action == "movies":
            return User.objects
        return Movie.objects

    @action(methods=["get"], detail=True)
    def movies(self, request, pk=None, **kwargs):
        user = self.get_object()
        movie_list = MovieList.objects.filter(owner=user, name=RECOMMENDATION).first()
        movies = []
        if movie_list:
            movies = movie_list.movies.all()
        logger.debug(f"{pk} {user} {movies}")
        return Response(data=MovieSerializerSummary(instance=movies, many=True).data)

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
        self._add_to_contest_recommend(movie, user)
        recommendation_list, _ = MovieList.objects.get_or_create(
            owner=user, name=RECOMMENDATION
        )
        logger.debug(f"{recommendation_list}")
        recommendation_list.movies.add(movie)
        recommendation_list.save()
        return response.Response(dict(success=True))

    def destroy(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        self._remove_from_contest_recommend(movie, user)
        recommendation_list = MovieList.objects.get(owner=user, name=RECOMMENDATION)
        if recommendation_list:
            recommendation_list.movies.remove(movie)
            recommendation_list.save()
        return response.Response(dict(success=True))


class IsMovieListOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, object: MovieList):
        me = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        return object.owner == me


class MovieListView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsMovieListOwner]
    queryset = MovieList.objects.annotate(
        likes=Count("liked_by"), number_of_movies=Count("movies")
    ).exclude(name=RECOMMENDATION)
    filterset_fields = ["owner__id"]
    ordering_fields = ["movies", "likes"]
    ordering = ["likes"]

    def get_serializer_class(self):
        logger.debug(self.action)
        if self.action == "retrieve":
            return MovieListDetailSerializer
        return MovieListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


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
            return True

        director = Role.objects.get(name="Director")
        return Movie.objects.filter(
            id=object.movie.id,
            crewmember__role=director,
            crewmember__profile=me.profile,
        ).exists()


class CrewMemberRequestView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsDirectorCreatorOrRequestor]
    serializer_class = CrewMemberRequestSerializer
    filterset_fields = ["requestor__id"]

    def get_queryset(self):
        return CrewMemberRequest.objects

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class ContestView(viewsets.GenericViewSet):
    queryset = Contest.objects.all()
    ordering_fields = []

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "top_creators":
            return TopCreatorSerializer
        else:
            return TopCuratorSerializer

    @action(
        methods=["get"], detail=True, url_path="top-creators",
    )
    def top_creators(self, request, pk=None, **kwargs):
        contest = self.get_object()
        top_creators = contest.top_creators.all()
        return self._paginated_response(top_creators)

    @action(
        methods=["get"], detail=True, url_path="top-curators",
    )
    def top_curator(self, request, pk=None, **kwargs):
        contest = self.get_object()
        top_curators = contest.top_curators.all()
        return self._paginated_response(top_curators)

    def _paginated_response(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(instance=page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(instance=queryset, many=True)
        return response.Response(serializer.data)
