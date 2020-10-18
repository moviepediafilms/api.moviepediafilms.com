from logging import getLogger

from django.db.models import Count

from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins, exceptions, parsers
from api.serializers.movie import (
    SubmissionSerializer,
    MoviePosterSerializer,
    MovieLanguageSerializer,
    MovieGenreSerializer,
    MovieSerializer,
    MovieReviewDetailSerializer,
)
from api.models import Movie, MoviePoster, MovieLanguage, MovieGenre, MovieRateReview

logger = getLogger("app.view")


class SubmissionView(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet,
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
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet,
):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as ex:
            logger.exception(ex)
            raise exceptions.ParseError(dict(error=str(ex)))


class MoviePosterView(ModelViewSet):
    queryset = MoviePoster.objects.all()
    serializer_class = MoviePosterSerializer


class MovieLanguageView(GenericViewSet, mixins.ListModelMixin):
    queryset = MovieLanguage.objects.all()
    serializer_class = MovieLanguageSerializer


class MovieGenreView(GenericViewSet, mixins.ListModelMixin):
    queryset = MovieGenre.objects.all()
    serializer_class = MovieGenreSerializer


class MovieReviewView(
    GenericViewSet,
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


from rest_framework.response import Response


class MovieReviewLikeView(
    GenericViewSet, mixins.DestroyModelMixin, mixins.UpdateModelMixin
):
    queryset = MovieRateReview.objects.all()

    def update(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        instance.liked_by.add(user)
        instance.save()
        return Response(dict(success=True))

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        instance.liked_by.remove(user)
        instance.save()
        return Response(dict(success=True))


class MovieWatchlistView(
    GenericViewSet, mixins.DestroyModelMixin, mixins.UpdateModelMixin
):
    queryset = Movie.objects.all()

    def update(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        user.profile.watchlist.add(movie)
        user.profile.save()
        return Response(dict(success=True))

    def destroy(self, request, *args, **kwargs):
        user = request.user
        movie = self.get_object()
        user.profile.watchlist.remove(movie)
        user.profile.save()
        return Response(dict(success=True))
