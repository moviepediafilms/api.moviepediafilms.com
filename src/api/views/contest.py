from logging import getLogger

from django.utils import timezone

from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, viewsets, response
from rest_framework.decorators import action

from api.constants import CONTEST_STATE
from api.serializers.contest import ContestRecommendListSerializer
from api.serializers.movie import (
    ContestSerializer,
    MovieSerializerSummary,
    TopCreatorSerializer,
    TopCuratorSerializer,
)
from api.models import Contest, TopCurator, TopCreator
from .utils import paginated_response

logger = getLogger(__name__)


class ContestView(viewsets.GenericViewSet, mixins.ListModelMixin):
    ordering_fields = ["start"]
    filterset_fields = ["type__name"]

    def get_queryset(self):
        base_qs = Contest.objects.all()
        live = self.request.query_params.get("live", None)
        if live is not None:
            now = timezone.now()
            if live == "true":
                base_qs = base_qs.filter(
                    start__lte=now, end__gte=now, state=CONTEST_STATE.LIVE
                )
            elif live == "false":
                base_qs = base_qs.exclude(start__lte=now, end__gte=now)
        return base_qs

    def get_serializer_class(self, *args, **kwargs):
        logger.debug(f"action {self.action}")
        return {
            "top_creators": TopCreatorSerializer,
            "top_curators": TopCuratorSerializer,
            "my_creator_position": TopCreatorSerializer,
            "my_curator_position": TopCuratorSerializer,
            "recommend": ContestRecommendListSerializer,
            "movies": MovieSerializerSummary,
        }.get(self.action, ContestSerializer)

    @action(
        methods=["get"],
        detail=True,
        url_path="top-creators",
    )
    def top_creators(self, request, pk=None, **kwargs):
        contest = self.get_object()
        top_creators = contest.top_creators.order_by("pos").all()
        return paginated_response(self, top_creators)

    @action(
        methods=["get"],
        detail=True,
        url_path="top-curators",
    )
    def top_curators(self, request, pk=None, **kwargs):
        contest = self.get_object()
        top_curators = contest.top_curators.order_by("pos").all()
        return paginated_response(self, top_curators)

    @action(methods=["get", "post", "delete"], detail=True, url_path="recommend")
    def recommend(self, request, pk=None, **kwargs):
        contest = self.get_object()
        action = {"POST": "add", "DELETE": "remove"}.get(request.method)
        if action:
            serializer = self.get_serializer(
                instance=contest,
                data=request.data,
                context={"request": request, "action": action},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer = self.get_serializer(
                instance=contest, context={"request": request}
            )
        return response.Response(serializer.data)

    @action(methods=["get"], detail=True)
    def movies(self, request, **kwargs):
        contest = self.get_object()
        movies_qs = contest.movies.order_by("-publish_on", "-recommend_count", "title")
        return paginated_response(self, movies_qs)

    @action(methods=["get"], detail=True, permission_classes=[IsAuthenticated])
    def my_creator_position(self, request, **kwargs):
        contest = self.get_object()
        top_creator = get_object_or_404(
            TopCreator.objects, contest=contest, profile=request.user.profile
        )
        serializer = self.get_serializer(instance=top_creator)
        return response.Response(data=serializer.data)

    @action(methods=["get"], detail=True, permission_classes=[IsAuthenticated])
    def my_curator_position(self, request, **kwargs):
        contest = self.get_object()
        top_curator = get_object_or_404(
            TopCurator.objects, contest=contest, profile=request.user.profile
        )
        serializer = self.get_serializer(instance=top_curator)
        return response.Response(data=serializer.data)
