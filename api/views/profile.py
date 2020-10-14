from logging import getLogger
from rest_framework.viewsets import ModelViewSet
from api.serializers.profile import ProfileDetailSerializer, RoleSerializer
from api.models import Profile, Role

logger = getLogger("app.view")


class ProfileView(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileDetailSerializer
    lookup_field = "user__id"


class RoleView(ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
