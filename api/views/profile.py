from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from api.serializers.profile import ProfileSerializer
from api.models import Profile


class ProfileView(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
