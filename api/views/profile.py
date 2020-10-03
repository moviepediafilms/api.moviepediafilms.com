from logging import getLogger
from rest_framework.viewsets import ModelViewSet
from api.serializers.profile import ProfileSerializer
from api.models import Profile

logger = getLogger("app.view")


class ProfileView(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    lookup_field = "user__id"
