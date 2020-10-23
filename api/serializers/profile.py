from logging import getLogger
from rest_framework import serializers, validators
from django.contrib.auth.models import User
from django.db import transaction

from api.models import Profile, Role, Movie


logger = getLogger("app.serializer")


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True, allow_blank=True)
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
        ]
    )
    password = serializers.CharField(min_length=6, write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "username",
            "name",
            "password",
        ]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["name", "id"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    profile_id = serializers.IntegerField(source="id")

    class Meta:
        model = Profile
        fields = ["profile_id", "user", "image"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.update(representation.pop("user"))
        return representation


class WatchListMovieSerializer(serializers.ModelSerializer):
    director = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ["id", "title", "link", "runtime", "director"]

    def get_director(self, movie):
        logger.debug("getting director")
        director_role = Role.objects.get(name="Director")
        logger.debug(f"Role: {director_role}")
        director_crew_relation = movie.crewmember_set.filter(role=director_role).first()
        if director_crew_relation:
            logger.debug(f"Crew: {director_crew_relation}")
            return ProfileSerializer(instance=director_crew_relation.profile).data


class ProfileDetailSerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source="id", read_only=True)
    user = UserSerializer()
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "profile_id",
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
        logger.debug(f"profile::create {validated_data}")
        user_data = validated_data.pop("user")
        with transaction.atomic():
            user = UserSerializer().create(validated_data=user_data)
            user.set_password(user_data.pop("password"))
            user.save()
            profile = Profile.objects.create(user=user, **validated_data)
        logger.debug(f"profile::create successful {profile.id}")
        return profile

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.update(representation.pop("user"))
        return representation
