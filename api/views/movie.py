from logging import getLogger
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import CreateAPIView
from rest_framework import mixins
from rest_framework import parsers
from api.serializers.movie import (
    SubmissionSerializer,
    MoviePosterSerializer,
    MovieLanguageSerializer,
    MovieGenreSerializer,
)
from api.models import Movie, MoviePoster, MovieLanguage, MovieGenre

logger = getLogger("app.view")


class SubmissionView(CreateAPIView):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    serializer_class = SubmissionSerializer

    def perform_create(self, serializer):
        logger.info(f"[submission] start  {self.request.user.email}")
        serializer.save(user=self.request.user)
        logger.info(f"[submission] end")


class MoviePosterView(ModelViewSet):
    queryset = MoviePoster.objects.all()
    serializer_class = MoviePosterSerializer


class MovieLanguageView(GenericViewSet, mixins.ListModelMixin):
    queryset = MovieLanguage.objects.all()
    serializer_class = MovieLanguageSerializer


class MovieGenreView(GenericViewSet, mixins.ListModelMixin):
    queryset = MovieGenre.objects.all()
    serializer_class = MovieGenreSerializer
