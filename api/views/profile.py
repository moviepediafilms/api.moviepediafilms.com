from logging import getLogger
from rest_framework import permissions, viewsets
from api.serializers.profile import ProfileDetailSerializer, RoleSerializer
from api.models import Profile, Role

logger = getLogger("app.view")


class ProfileView(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileDetailSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    lookup_field = "user__id"


class RoleView(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
