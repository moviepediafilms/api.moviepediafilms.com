from logging import getLogger
import requests
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer
from api.emails import email_trigger, TEMPLATES

logger = getLogger("api.serializer")


class TokenSerializer(AuthTokenSerializer):
    def validate(self, attrs):
        username = attrs.get("username")

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # let super call raise a proper error
                pass
            else:
                if not user.is_active:
                    raise ValidationError(
                        "Your account is not active, please verify your account before login"
                    )
        return super().validate(attrs)


class VerifyEmailSerializer(Serializer):
    def save(self, **kwargs):
        token = self.instance
        logger.info(f"{token.user} is now verified")
        token.user.is_active = True
        token.user.save()
        token.delete()


class ActivationResentSerializer(Serializer):
    email = serializers.EmailField(
        required=True, error_messages={"required": _("You must provide email")}
    )

    def save(self, **kwargs):
        email = self.validated_data["email"]
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            # fail silently for security reasons
            logger.error(f"Accont activation requested for unregistered email: {email}")
            pass
        else:
            profile = getattr(user, "profile", None)
            logger.info(f"Accont activation requested for registered email: {email}")
            if not profile:
                logger.error("User does  not have a profile associated with him")
                return
            email_trigger(
                profile.user, TEMPLATES.VERIFY, fail_silently=False,
            )


class ForgotPasswordSerializer(Serializer):
    email = serializers.EmailField(
        required=True, error_messages={"required": _("You must provide email")}
    )
    recaptcha = serializers.CharField(
        required=True, error_messages={"required": _("You must check this")}
    )

    def validate_recaptcha(self, recaptcha):
        try:
            res = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                {
                    "secret": getattr(settings, "RECAPTCHA_SECRET_KEY"),
                    "response": recaptcha,
                },
            )
        except Exception as ex:
            logger.error(ex)
            raise ValidationError("Couldn't verify Captcha, please try again later!")
        else:
            logger.debug(f"google reply: {res.json()}")
            if not res.json().get("success"):
                raise ValidationError(
                    "Captcha verification failed, please try again later!"
                )
        return recaptcha

    def save(self, **kwargs):
        email = self.validated_data["email"]
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            # Invalid email supplied
            # fail silently for security reasons
            pass
        else:
            email_trigger(user, TEMPLATES.PASSWORD_REST)


class ResetPasswordSerializer(Serializer):
    password = serializers.CharField(required=True, min_length=6)

    def save(self, **kwargs):
        token = self.instance
        token.user.set_password(self.validated_data["password"])
        token.user.save()
        token.delete()
