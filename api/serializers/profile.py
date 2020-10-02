from logging import getLogger
from rest_framework import serializers, validators
from django.contrib.auth.models import User
from django.db.models import Sum
from django.db import transaction

from api.models import Profile, BadgeClaim, Role
from api.constants import CLAIM_STATE


logger = getLogger("app.serializer")


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(
        validators=[
            validators.UniqueValidator(
                queryset=User.objects.all(), message="This email is already in use.",
            )
        ],
        write_only=True,
    )
    email = serializers.CharField(
        validators=[
            validators.UniqueValidator(
                queryset=User.objects.all(), message="This email is already in use.",
            )
        ],
        write_only=True,
    )
    password = serializers.CharField(min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username", "name", "password"]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["name", "id"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    roles = RoleSerializer(many=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "city",
            "dob",
            "gender",
            "mobile",
            "roles",
            "image",
            "level",
            "rank",
            "score",
            "mcoins",
            "pop_score",
        ]

    def create(self, validated_data: dict):
        logger.debug(validated_data)
        user_data = validated_data.pop("user")
        roles_data = validated_data.pop("roles")
        roles = Role.objects.filter(name__in=[rd.get("name") for rd in roles_data])

        with transaction.atomic():
            user = UserSerializer().create(validated_data=user_data)
            user.set_password(user_data.pop("password"))
            user.save()

            profile = Profile.objects.create(user=user, **validated_data)
            profile.roles.set(roles)
        logger.debug("Profile created successfully")
        return profile

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.update(representation.pop("user"))
        return representation
