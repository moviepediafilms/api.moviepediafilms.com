from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import generics
from api.serializers.auth import TokenSerializer


class AuthTokenView(ObtainAuthToken):
    "Auth view expects `username` and `password` as POST payload"

    serializer_class = TokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.email})


class VerifyEmail(generics.RetrieveAPIView):
    def get(self, request, token=None, **kwargs):
        status = 200
        try:
            token = Token.objects.get(key=token)
        except Token.DoesNotExist:
            status = 400
        else:
            token.user.is_active = True
            token.user.save()
        data = {
            200: {"message": "Account verified! please proceed to login"},
            400: {"error": "Account verification failed! link has expired."},
        }[status]
        return Response(status=status, data=data)
