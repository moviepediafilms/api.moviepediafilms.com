from logging import getLogger
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, exceptions, parsers

from api.serializers.movie import (
    SubmissionSerializer,
    MoviePosterSerializer,
    MovieLanguageSerializer,
    MovieGenreSerializer,
    MovieSerializer,
)
from api.models import Movie, MoviePoster, MovieLanguage, MovieGenre

logger = getLogger("app.view")


class SubmissionView(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    permission_classes = [IsAuthenticated]
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
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
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
