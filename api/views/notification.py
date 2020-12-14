from rest_framework import views
from rest_framework.response import Response


class NotificationListView(views.APIView):
    def get(self, request, format=None):
        usernames = []
        return Response(usernames)
