from logging import getLogger
from rest_framework import serializers, validators
from django.contrib.auth.models import User
from django.db import transaction
from django.conf import settings
from django.core.files.storage import default_storage
import os
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
            "follows",
        ]
        read_only_fields = ["level", "rank", "score", "mcoins", "pop_score", "follows"]

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


class FollowSerializer(serializers.ModelSerializer):
    follow = serializers.BooleanField(write_only=True)

    class Meta:
        model = Profile
        fields = ["follow", "follows"]

    def update(self, profile_to_follow, validated_data):
        user = validated_data.get("user")
        if validated_data.get("follow"):
            user.profile.follows.add(profile_to_follow)
        else:
            user.profile.follows.remove(profile_to_follow)
        user.profile.save()
        return user.profile


class ProfileImageSerializer(serializers.Serializer):
    image = serializers.ImageField()

    class Meta:
        model = Profile
        fields = ["image"]

    def update(self, profile, validated_data):
        image = validated_data.get("image")
        image_url = self._write_image(image, profile)
        profile.image = image_url
        profile.save()
        return profile

    def _write_image(self, image, profile):
        if not image:
            return
        ext = image.name.split(".")[-1]
        image_filename = f"{profile.id:010d}.{ext}"
        image_path = os.path.join(settings.MEDIA_PROFILE, image_filename)
        if default_storage.exists(image_path):
            default_storage.delete(image_path)
        image_filename = default_storage.save(image_path, image)
        url = default_storage.url(image_filename)
        logger.debug(f"image saved at: {url}")
        return url

    def to_representation(self, instance):
        return ProfileDetailSerializer(instance=instance).data
