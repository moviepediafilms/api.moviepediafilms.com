from django.db.models.query import EmptyQuerySet
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import generics, viewsets, mixins
from api.serializers.auth import (
    TokenSerializer,
    VerifyEmailSerializer,
    ActivationResentSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


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


class AccountVerifyView(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    permission_classes = []
    queryset = Token.objects

    def get_serializer_class(self):
        return {
            "verify": VerifyEmailSerializer,
            "resend": ActivationResentSerializer,
            "forgot": ForgotPasswordSerializer,
            "reset": ResetPasswordSerializer,
        }[self.action]

    @action(methods=["get"], detail=True)
    def verify(self, request, *args, **kwargs):
        self.update(request, *args, **kwargs)
        return Response({"success": True})

    @action(methods=["post"], detail=False)
    def resend(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True})

    @action(methods=["post"], detail=False)
    def forgot(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True})

    @action(methods=["post"], detail=True)
    def reset(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"success": True})
