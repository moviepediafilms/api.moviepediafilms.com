from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from api.models.movie import CrewMember
import os
import uuid
from logging import getLogger

from django.contrib.auth.models import User
from django.db import transaction
from django.conf import settings
from django.core.files.storage import default_storage

from rest_framework import serializers
from PIL import Image

from api.models import Profile, Role, Movie, Notification
from api.constants import MOVIE_STATE, DEFAULT_AVATARS

logger = getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True, allow_blank=True)
    email = serializers.EmailField(required=True, write_only=True)
    password = serializers.CharField(min_length=6, write_only=True)
    image = serializers.URLField(source="profile.image", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "name",
            "password",
            "image",
        ]
        extra_kwargs = {"email": {"write_only": True}}

    def validate_email(self, email):
        email = email.lower()
        if self.instance:
            email = self.instance.email
        else:
            if User.objects.filter(email=email).exists():
                raise ValidationError("This email is already in use.")
        return email

    def validate_first_name(self, first_name):
        return first_name and first_name.title()

    def validate_last_name(self, last_name):
        return last_name and last_name.title()

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data["username"] = validated_data.get("email")
        validated_data["is_active"] = False
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        super().update(instance, validated_data)
        instance.set_password(password)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not representation.get("image"):
            profile = getattr(instance, "profile", None)
            if profile:
                representation["image"] = DEFAULT_AVATARS.get(instance.profile.gender)
        return representation


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["name", "id"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    profile_id = serializers.IntegerField(source="id")

    class Meta:
        model = Profile
        fields = [
            "profile_id",
            "user",
            "image",
            "creator_rank",
            "curator_rank",
            "level",
            "is_celeb",
            "engagement_score",
            "pop_score",
            "city",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.update(representation.pop("user"))
        if not representation.get("image"):
            representation["image"] = DEFAULT_AVATARS.get(instance.gender)
        return representation


# TODO: not used, check and remove the class
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
    token = serializers.CharField(required=False, write_only=True)
    profile_id = serializers.IntegerField(source="id", read_only=True)
    user = UserSerializer()
    roles = RoleSerializer(many=True, read_only=True)
    movies_directed = serializers.SerializerMethodField(read_only=True)
    about = serializers.SerializerMethodField(read_only=True)
    title = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "token",
            "profile_id",
            "user",
            "about",
            "title",
            "city",
            "dob",
            "gender",
            "mobile",
            "roles",
            "image",
            "is_celeb",
            "level",
            "creator_rank",
            "curator_rank",
            "engagement_score",
            "mcoins",
            "pop_score",
            "follows",
            "movies_directed",
        ]
        read_only_fields = ["level", "rank", "score", "mcoins", "pop_score", "follows"]
        extra_kwargs = {"mobile": {"write_only": True}, "dob": {"write_only": True}}

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        request = self.context.get("request", None)
        if request and getattr(request, "method", None) == "PATCH":
            fields["token"].required = True
        return fields

    def create(self, validated_data: dict):
        logger.debug(f"profile::create {validated_data}")
        user_data = validated_data.pop("user")
        profile = None
        with transaction.atomic():
            user = UserSerializer().create(validated_data=user_data)
            profile = Profile.objects.create(user=user, **validated_data)
        logger.debug(f"profile::create successful {profile.id}")
        return profile

    def update(self, instance, validated_data):
        token = validated_data.pop("token")
        user_data = validated_data.pop("user", {})
        validated_data["onboarded"] = True
        # cannot let user change his email address
        user_data.pop("email", None)
        user = UserSerializer().update(instance=token.user, validated_data=user_data)
        super().update(instance, validated_data)
        logger.debug(f"profile::update successful {user.profile.id}")
        return user.profile

    def validate_token(self, token):
        try:
            token = Token.objects.get(key=token)
        except Token.DoesNotExist:
            raise ValidationError("Invalid Token!")
        else:
            return token

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.update(representation.pop("user"))
        if not representation.get("image"):
            representation["image"] = DEFAULT_AVATARS.get(instance.gender)
        return representation

    def get_movies_directed(self, profile):
        director_role = Role.objects.filter(name="Director").first()
        return CrewMember.objects.filter(
            profile=profile, role=director_role, movie__state=MOVIE_STATE.PUBLISHED
        ).count()

    def get_title(self, profile):
        if profile.is_celeb and profile.about:
            return profile.about.split("\n", 1)[0]

    def get_about(self, profile):
        # first line of about in celeb profiles is considered as title
        if profile.is_celeb and profile.about:
            segs = profile.about.strip().split("\n", 1)
            return segs[1] if len(segs) > 1 else ""
        else:
            return profile.about


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
        image_url, img_name = self._write_image(image, profile)
        self._resize_image(img_name)
        self._delete_existing_profile_image(profile)
        profile.image = image_url
        profile.save()
        return profile

    def _get_thumb_path(self, dimen, img_name):
        thumb_name = f"{dimen}_{img_name}"
        return os.path.join(settings.MEDIA_PROFILE, thumb_name)

    def _resize_image(self, img_name):
        if not img_name:
            return
        img_abs_path = os.path.join(
            settings.MEDIA_ROOT, settings.MEDIA_PROFILE, img_name
        )

        logger.debug(f"resizing {img_abs_path}")
        try:
            img = Image.open(img_abs_path)
            img = img.resize((400, 400))
            img.save(img_abs_path)
            for dimen in settings.THUMB_DIMENS:
                tmp_img = img.resize((dimen, dimen))
                thumb_abs_path = os.path.join(
                    settings.MEDIA_ROOT, self._get_thumb_path(dimen, img_name)
                )
                tmp_img.save(thumb_abs_path)
        except Exception as ex:
            logger.debug("image resize failed")
            logger.exception(ex)
        else:
            logger.debug("image resized")

    def _delete_existing_profile_image(self, profile):
        if profile.image:
            old_image_name = profile.image.lstrip(
                settings.MEDIA_URL + settings.MEDIA_PROFILE
            )
            old_image_path = os.path.join(settings.MEDIA_PROFILE, old_image_name)
            files_to_del = []
            files_to_del.append(old_image_path)
            for dimen in settings.THUMB_DIMENS:
                files_to_del.append(self._get_thumb_path(dimen, old_image_name))

            logger.debug(f"deleting files at {files_to_del}")
            for file_path in files_to_del:
                if default_storage.exists(file_path):
                    default_storage.delete(file_path)

    def _write_image(self, image, profile):
        if not image:
            return
        ext = image.name.split(".")[-1]
        image_filename = f"{uuid.uuid4()}.{ext}"
        image_path = os.path.join(settings.MEDIA_PROFILE, image_filename)
        image_path = default_storage.save(image_path, image)
        url = default_storage.url(image_path)
        logger.debug(f"image saved at: {url}")
        return url, image_filename

    def to_representation(self, instance):
        return ProfileDetailSerializer(instance=instance).data


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "content", "created_at"]
