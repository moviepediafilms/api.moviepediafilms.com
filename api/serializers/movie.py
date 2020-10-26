from logging import getLogger
import hashlib
import os

from django.conf import settings
from django.db.models import Avg
from django.db import transaction
from django.core.files.storage import default_storage
from rest_framework import serializers
from collections import defaultdict
import razorpay

from api.constants import MOVIE_STATE, CREW_MEMBER_REQUEST_STATE
from api.models import (
    User,
    Movie,
    MovieGenre,
    MovieLanguage,
    MoviePoster,
    Order,
    Package,
    Profile,
    Role,
    CrewMember,
    MovieRateReview,
    MovieList,
    CrewMemberRequest,
)
from .profile import ProfileSerializer, UserSerializer

logger = getLogger("app.serializer")

rzp_client = razorpay.Client(
    auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET)
)


class MovieGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieGenre
        fields = ["id", "name"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["name"] = representation["name"].title()
        return representation


class MovieLanguageSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=50)

    class Meta:
        model = MovieLanguage
        fields = ["id", "name"]

    def validate_name(self, name):
        name = name.strip().lower()
        return name

    def create(self, validated_data):
        name = validated_data.get("name")
        try:
            lang = MovieLanguage.objects.get(name=name)
            logger.debug(f"language `{name}` exists")
        except MovieLanguage.DoesNotExist:
            lang = MovieLanguage.objects.create(name=name)
            logger.debug(f"New language `{name}` added")
        return lang

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["name"] = representation["name"].title()
        return representation


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["name"]


def create_rzp_order(package, owner):
    if not all([package, owner]):
        return
    existing_orders = Order.objects.filter(owner=owner).count()
    receipt_number = hashlib.md5(
        f"{owner.email}:{existing_orders}".encode()
    ).hexdigest()
    try:
        rp_order_res = rzp_client.order.create(
            {
                "amount": package.amount,
                "currency": "INR",
                "receipt": receipt_number,
                "payment_capture": 1,
                "notes": {"email": owner.email},
            }
        )
    except Exception:
        logger.error("Exception in creating Razorpay order")
        raise
    else:
        if rp_order_res.get("status") != "created":
            logger.error(f"Error response from razorpay: {rp_order_res}")
            raise Exception("Error creating Razorpay order")
        return rp_order_res


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["owner", "order_id", "amount"]


class PackageSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    amount = serializers.FloatField()

    class Meta:
        model = Package
        fields = ["name", "amount"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["name"] = representation.get("name", "").title()
        return representation


class DirectorSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField(allow_blank=True)
    email = serializers.EmailField()
    contact = serializers.CharField(min_length=10)


class CrewMemberSerializer(serializers.Serializer):
    roles = RoleSerializer(many=True)
    profile = ProfileSerializer()


class MovieSerializerSummary(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "poster",
        ]


class MovieSerializer(serializers.ModelSerializer):
    order = OrderSerializer(required=False)
    lang = MovieLanguageSerializer()
    genres = MovieGenreSerializer(many=True)
    package = PackageSerializer(required=False)
    director = DirectorSerializer(write_only=True, required=False)
    # Roles of the user(Profile) who submitted the movie (Creator roles)
    roles = RoleSerializer(write_only=True, many=True)
    crew = serializers.SerializerMethodField()
    requestor_rating = serializers.SerializerMethodField(read_only=True)
    # is watch listed by the requestor if he is authenticated
    is_watchlisted = serializers.SerializerMethodField(read_only=True)
    # is recommended by the requestor if he is authenticated
    is_recommended = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "order",
            "title",
            "link",
            "runtime",
            "genres",
            "lang",
            "poster",
            "package",
            "crew",
            "director",
            "roles",
            "jury_rating",
            "audience_rating",
            "requestor_rating",
            "is_watchlisted",
            "is_recommended",
            "publish_on",
        ]

    def get_requestor_rating(self, movie):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            review = MovieRateReview.objects.filter(
                movie=movie, author=request.user
            ).first()
            return MovieReviewSerializer(instance=review).data
        return False

    def get_is_recommended(self, movie):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            recommendation_list = MovieList.objects.filter(
                owner=request.user, name="Recommendation"
            ).first()
            if recommendation_list:
                return recommendation_list.movies.filter(id=movie.id).exists()
        return False

    def get_is_watchlisted(self, movie):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return movie.watchlisted_by.filter(user=request.user).exists()
        return False

    def get_crew(self, movie):
        # since one user can have multiple roles, we can
        # reduce the number of items returned by grouping the crew relationship by user
        group_by_user = defaultdict(list)
        for crewmember in movie.crewmember_set.all():
            group_by_user[crewmember.profile].append(crewmember.role)
        data = [
            {"profile": profile, "roles": roles}
            for profile, roles in group_by_user.items()
        ]
        serializer = CrewMemberSerializer(many=True, instance=data)
        return serializer.data

    def validate_package(self, package):
        logger.debug(f"validate_package::{package}")

        if package and self.instance.package:
            logger.warn("Cannot update package")
            raise serializers.ValidationError("Cannot update package")

        package_name = package.get("name")
        package_name = package_name.strip().lower()
        if not Package.objects.filter(name=package_name).exists():
            logger.warn("Invalid package selected")
            raise serializers.ValidationError("Invalid Package Selected")
        return package

    def create(self, validated_data: dict):
        logger.debug(f"create::{validated_data}")
        user = validated_data.pop("user")
        genres_data = validated_data.pop("genres")
        creator_roles = validated_data.pop("roles")
        lang_data = validated_data.pop("lang")
        director_data = validated_data.pop("director", None)

        validated_data["lang"] = MovieLanguageSerializer().create(lang_data)
        # creating dummy order here so that the movie entry can be tracked
        # back to the creator using movie.order.owner
        validated_data["order"] = Order.objects.create(owner=user)
        validated_data["state"] = MOVIE_STATE.SUBMITTED
        movie = super().create(validated_data)
        movie.genres.set(self._get_or_create_genres(genres_data))
        self._attach_director_role(director_data, user, movie)
        self._attach_creator_roles(creator_roles, user, movie)
        return movie

    def update(self, movie, validated_data):
        logger.debug(f"update::{validated_data}")
        user = validated_data.pop("user")
        package_data = None
        if "package" in validated_data:
            package_data = validated_data.pop("package")
            # If package was not earlier set
            package_name = package_data.get("name").strip().lower()
            movie.package = Package.objects.get(name=package_name)
            rzp_order = create_rzp_order(movie.package, movie.order.owner)
            self._update_order_details(movie, rzp_order)
        if "lang" in validated_data:
            lang_data = validated_data.pop("lang")
            validated_data["lang"] = MovieLanguageSerializer().create(lang_data)

        director_data = validated_data.pop("director", None)
        self._attach_director_role(director_data, user, movie)
        if "roles" in validated_data:
            creator_roles = validated_data.pop("roles")
            self._attach_creator_roles(creator_roles, user, movie)
        genres_data = None
        if "genres" in validated_data:
            genres_data = validated_data.pop("genres")

        movie = super().update(movie, validated_data)

        if genres_data:
            movie.genres.set(self._get_or_create_genres(genres_data))
        return movie

    def _attach_director_role(self, director_data: dict, creator: User, movie: Movie):
        director_role = Role.objects.get(name="Director")
        if director_data:
            # creator is not the director
            contact = director_data.pop("contact")
            email = director_data.get("email")
            director_data["username"] = email
            try:
                # check if the director is already registered
                director_profile = Profile.objects.get(user__email=email)
            except Profile.DoesNotExist:
                # creating a new profile
                user = User.objects.create(**director_data)
                director_profile = Profile.objects.create(user=user, mobile=contact)
        else:
            director_profile = Profile.objects.get(user__id=creator.id)
        # remove existing director relation on movie
        CrewMember.objects.filter(role=director_role, movie=movie).delete()
        CrewMember.objects.create(
            profile=director_profile, movie=movie, role=director_role
        )

    def _attach_creator_roles(
        self, creator_roles_data: list, creator: User, movie: Movie
    ):
        director_role = Role.objects.get(name="Director")
        creator_role_names = [
            role.get("name")
            for role in creator_roles_data
            if role.get("name") != "Director"
        ]
        creator_roles = Role.objects.filter(name__in=creator_role_names).all()
        logger.debug(f"creator_roles:{creator_roles}")
        creator_profile = Profile.objects.get(user__id=creator.id)
        # clear all roles of creator
        CrewMember.objects.filter(movie=movie, profile=creator_profile).exclude(
            role__in=[director_role]
        ).delete()
        # add all roles of creator
        for creator_role in creator_roles:
            CrewMember.objects.create(
                profile=creator_profile, movie=movie, role=creator_role
            )
        logger.debug(f"crew::{movie.crewmember_set.all()}")

    def _update_order_details(self, movie, rzp_order):
        logger.debug(f"_update_order::{rzp_order}")
        if not movie or not rzp_order:
            return
        order = movie.order
        order.order_id = rzp_order.get("id")
        order.amount = rzp_order.get("amount")
        order.receipt_number = rzp_order.get("receipt")
        order.save()

    def _get_or_create_genres(self, genres_data):
        names = [name.get("name") for name in genres_data]
        names = [name.strip().lower() for name in names if name]
        existing_genres = list(MovieGenre.objects.filter(name__in=names).all())
        existing_genre_names = [genre.name for genre in existing_genres]
        for name in names:
            if name not in existing_genre_names:
                genre = MovieGenre.objects.create(name=name)
                logger.debug(f"Creating Genre `{name}`")
                existing_genres.append(genre)
        return existing_genres

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for float_key in ["audience_rating", "jury_rating"]:
            value = data.get(float_key)
            if value:
                data[float_key] = "{:.1f}".format(value)
        return data


class SubmissionSerializer(serializers.Serializer):
    poster = serializers.ImageField(required=False)
    payload = serializers.JSONField()

    def validate_payload(self, payload):
        logger.debug(f"validate_payload::{payload}")
        serializer = MovieSerializer(
            data=payload, partial=self.partial, instance=self.instance
        )
        serializer.is_valid(raise_exception=True)
        return payload

    def create(self, validated_data):
        logger.debug(f"create::{validated_data}")
        payload = validated_data["payload"]
        payload["user"] = validated_data["user"]
        movie = MovieSerializer().create(payload)
        movie.poster = self._save_poster(validated_data, movie.id)
        logger.debug("create::end")
        return movie

    def update(self, instance, validated_data):
        logger.debug(f"update::{validated_data}")
        payload = validated_data.get("payload")
        payload["user"] = validated_data["user"]
        movie = MovieSerializer().update(instance, payload)
        movie.poster = self._save_poster(validated_data, movie.id)
        logger.debug("update::end")
        return movie

    def to_representation(self, instance):
        return MovieSerializer().to_representation(instance)

    def _save_poster(self, validated_data, movie_id):
        if not validated_data:
            return
        if "poster" in validated_data:
            poster_file = validated_data.get("poster")
            return self._write_poster(poster_file, movie_id)

    def _write_poster(self, poster, movie_id):
        if not poster:
            return
        ext = poster.name.split(".")[-1]
        poster_filename = f"{movie_id:010d}.{ext}"
        poster_path = os.path.join(settings.MEDIA_POSTERS, poster_filename)
        if default_storage.exists(poster_path):
            default_storage.delete(poster_path)
        poster_filename = default_storage.save(poster_path, poster)
        url = default_storage.url(poster_filename)
        logger.debug(f"poster saved at: {url}")
        return url


class MoviePosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoviePoster
        fields = ["link", "primary", "movie"]


class MovieReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieRateReview
        fields = ["id", "content", "rating"]


class MinUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name")

    class Meta:
        model = User
        fields = ["id", "name"]


class MovieReviewDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    liked_by = MinUserSerializer(read_only=True, many=True)
    # serializers.IntegerField(source="liked_by.count", read_only=True)
    published_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = MovieRateReview
        fields = [
            "id",
            "author",
            "content",
            "liked_by",
            "published_at",
            "rating",
            "movie",
        ]

    def validate(self, validated_data):
        if all([key not in validated_data for key in ["content", "rating"]]):
            raise serializers.ValidationError(
                "Atleast one of `content` or `rating` should be provided"
            )
        return validated_data

    def _update_movie_audience_rating(self, movie):
        if movie is not None:
            # FIXME: this average audience rating update might get into concurrency issue
            # a better way(IMO) will be to cache the average rating of movies via a job periodically
            movie.audience_rating = (
                MovieRateReview.objects.filter(movie=movie)
                .exclude(rating__isnull=True)
                .aggregate(Avg("rating"))
            ).get("rating__avg")
            movie.save()

    def create(self, validated_data):
        validated_data["author"] = validated_data.pop("user")
        instance = super().create(validated_data)
        self._update_movie_audience_rating(instance.movie)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._update_movie_audience_rating(instance.movie)
        return instance


class MovieListSerializer(serializers.ModelSerializer):
    like_count = serializers.IntegerField(source="likes", read_only=True)
    owner = serializers.PrimaryKeyRelatedField(source="owner.id", read_only=True)

    class Meta:
        model = MovieList
        fields = ["id", "owner", "name", "movies", "like_count"]

    def create(self, validated_data: dict):
        user = validated_data.pop("user")
        return MovieList.objects.create(**validated_data, owner=user)


class CrewMemberRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    requestor = UserSerializer(read_only=True)
    movie_detail = MovieSerializerSummary(read_only=True)

    name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    roles = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), many=True, write_only=True
    )

    class Meta:
        model = CrewMemberRequest
        fields = [
            "id",
            "name",
            "email",
            "roles",
            "movie",
            "requestor",
            "user",
            "role",
            "movie_detail",
            "state",
        ]
        read_only_fields = ["id", "requestor", "role", "user", "movie_detail", "state"]

    def _create_new_user(self, name, email):
        email = email.strip().lower()
        name_segs = [seg.strip() for seg in name.split(" ")]
        first_name = name_segs[0]
        last_name = " ".join(name_segs[1:])
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                first_name=first_name, last_name=last_name, username=email, email=email,
            )
        return user

    def create(self, validated_data):
        requestor = validated_data.pop("user")
        movie = validated_data.get("movie")
        validated_data["requestor"] = requestor
        email = validated_data.pop("email")
        name = validated_data.pop("name")
        instance = None
        director = Role.objects.get(name="Director")
        requestor_is_director_of_movie = CrewMember.objects.filter(
            profile__user=requestor, role=director, movie=movie
        ).exists()
        state = (
            CREW_MEMBER_REQUEST_STATE.APPROVED
            if requestor_is_director_of_movie
            else CREW_MEMBER_REQUEST_STATE.SUBMITTED
        )
        with transaction.atomic():
            user = self._create_new_user(name, email)
            validated_data["user"] = user
            for role in validated_data.pop("roles"):
                validated_data["role"] = role
                instance = CrewMemberRequest.objects.create(
                    **validated_data, state=state
                )
        return instance
