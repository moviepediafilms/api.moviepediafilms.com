from logging import getLogger

from django.db.models import Count

from rest_framework import mixins, exceptions, parsers, viewsets, response, permissions
from api.serializers.movie import (
    SubmissionSerializer,
    MoviePosterSerializer,
    MovieLanguageSerializer,
    MovieGenreSerializer,
    MovieSerializer,
    MovieReviewDetailSerializer,
    MovieListSerializer,
    CrewMemberRequestSerializer,
)
from api.models import (
    Movie,
    MoviePoster,
    MovieLanguage,
    MovieGenre,
    MovieRateReview,
    MovieList,
    CrewMemberRequest,
    Role,
)


logger = getLogger("app.view")


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
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

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
            return query.exclude(content__isnull=True)
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
    viewsets.GenericViewSet, mixins.DestroyModelMixin, mixins.UpdateModelMixin
):
    queryset = Movie.objects

    def update(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        recommendation_list, _ = MovieList.objects.get_or_create(
            owner=user, name="Recommendation"
        )
        logger.debug(f"{recommendation_list}")
        recommendation_list.movies.add(movie)
        recommendation_list.save()
        return response.Response(dict(success=True))

    def destroy(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        recommendation_list = MovieList.objects.get(owner=user, name="Recommendation")
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
    ).exclude(name="Recommendation")
    serializer_class = MovieListSerializer
    filterset_fields = ["owner__id"]
    ordering_fields = ["movies", "likes"]
    ordering = ["likes"]

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
