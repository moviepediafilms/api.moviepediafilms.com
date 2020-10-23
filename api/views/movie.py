from logging import getLogger

from django.db.models import Count

from rest_framework import mixins, exceptions, parsers, viewsets, response
from api.serializers.movie import (
    SubmissionSerializer,
    MoviePosterSerializer,
    MovieLanguageSerializer,
    MovieGenreSerializer,
    MovieSerializer,
    MovieReviewDetailSerializer,
    MovieListSerializer,
)
from api.models import (
    Movie,
    MoviePoster,
    MovieLanguage,
    MovieGenre,
    MovieRateReview,
    MovieList,
)


logger = getLogger("app.view")


class SubmissionView(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet,
):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    queryset = Movie.objects.all()

    def get_serializer_class(self):
        logger.debug(f"get_serializer_class::{self.action}")
        if self.action == "retrieve":
            return MovieSerializer
        else:
            return SubmissionSerializer

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


class MovieReviewView(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
):
    queryset = MovieRateReview.objects.annotate(
        number_of_likes=Count("liked_by")
    ).exclude(content__isnull=True)
    serializer_class = MovieReviewDetailSerializer
    filterset_fields = ["movie__id", "author__id"]
    ordering_fields = ["published_at", "number_of_likes"]
    ordering = [
        "-number_of_likes",
        "-published_at",
    ]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MovieReviewLikeView(
    viewsets.GenericViewSet, mixins.DestroyModelMixin, mixins.UpdateModelMixin
):
    queryset = MovieRateReview.objects.all()

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
    viewsets.GenericViewSet, mixins.DestroyModelMixin, mixins.UpdateModelMixin
):
    queryset = Movie.objects.all()

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
    queryset = Movie.objects.all()

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


class MovieListView(viewsets.ModelViewSet):
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
