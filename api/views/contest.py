from api.constants import CONTEST_STATE
from logging import getLogger
from django.utils import timezone
from rest_framework import mixins, viewsets, response
from rest_framework.decorators import action

from api.serializers.contest import ContestRecommendListSerializer
from api.serializers.movie import (
    ContestSerializer,
    MovieSerializerSummary,
    TopCreatorSerializer,
    TopCuratorSerializer,
)
from api.models import Contest
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
        top_creators = contest.top_creators.order_by("-score").all()
        return paginated_response(self, top_creators)

    @action(
        methods=["get"],
        detail=True,
        url_path="top-curators",
    )
    def top_curators(self, request, pk=None, **kwargs):
        contest = self.get_object()
        top_curators = contest.top_curators.order_by("-match").all()
        return paginated_response(self, top_curators)

    @action(methods=["get", "post", "delete"], detail=True, url_path="recommend")
    def recommend(self, request, pk=None, **kwargs):
        contest = self.get_object()
        action = {"POST": "add", "DELETE": "remove"}.get(request.method)
        if action:
            serializer = self.get_serializer(
                instance=contest, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user, action=action)
        else:
            serializer = self.get_serializer(
                instance=contest, context={"request": request}
            )
        return response.Response(serializer.data)

    @action(methods=["get"], detail=True)
    def movies(self, request, **kwargs):
        contest = self.get_object()
        return paginated_response(self, contest.movies.all())
