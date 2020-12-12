from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User


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
