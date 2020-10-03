from logging import getLogger
import hashlib

from django.conf import settings
from rest_framework import serializers
import razorpay

from api.models import Movie, MovieGenre, MovieLanguage, MoviePoster, Order

logger = getLogger("app.serializer")

rzp_client = razorpay.Client(
    auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET)
)


class MovieGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieGenre
        fields = ["name"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["name"] = representation["name"].title()
        return representation


class MovieLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieLanguage
        fields = ["name"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["name"] = representation["name"].title()
        return representation


def create_order(user):
    if not user:
        return
    existing_orders = Order.objects.filter(owner=user).count()
    receipt_number = hashlib.md5(f"{user.email}:{existing_orders}".encode()).hexdigest()
    amount = 29900  # in paise
    try:
        rp_order_res = rzp_client.order.create(
            {
                "amount": amount,
                "currency": "INR",
                "receipt": receipt_number,
                "payment_capture": 1,
                "notes": {"email": user.email},
            }
        )
    except Exception as ex:
        logger.error("Exception in creating Razorpay order")
        logger.exception(ex)
    else:
        if rp_order_res.get("status") != "created":
            logger.error(f"Error response from razorpay: {rp_order_res}")
        else:
            try:
                order = Order.objects.create(
                    owner=user,
                    amount=amount,
                    order_id=rp_order_res.get("id"),
                    receipt_number=rp_order_res.get("receipt"),
                )
            except Exception as ex:
                logger.error("Error creating Order object in backed")
                logger.exception(ex)
                order = None
            return order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["owner", "order_id", "amount"]


class MovieSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    lang = MovieLanguageSerializer()
    genres = MovieGenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            "order",
            "title",
            "link",
            "runtime",
            "genres",
            "lang",
        ]

    def create(self, validated_data: dict):
        logger.debug(validated_data)
        genre_names = validated_data.pop("genres")
        genres = MovieGenre.objects.filter(name__in=genre_names)
        lang_name = validated_data.pop("lang").get("name")
        try:
            lang = MovieLanguage.objects.get(name=lang_name)
        except MovieLanguage.DoesNotExist:
            logger.debug("Creating new language")
            lang_name = lang_name.strip().lower()
            lang = MovieLanguage.objects.create(name=lang_name)
        user = validated_data.pop("user")
        order = create_order(user)
        movie = Movie.objects.create(**validated_data, lang=lang, order=order)
        movie.genres.set(genres)
        return movie


class SubmissionSerializer(serializers.Serializer):
    poster = serializers.FileField(required=False)
    payload = serializers.JSONField()

    def validate_payload(self, payload):
        logger.debug(f"validate_payload {payload}")
        serializer = MovieSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        logger.debug(f"validated data: {serializer.data}")
        return serializer.data

    def create(self, validated_data):
        logger.debug(validated_data)
        payload = validated_data["payload"]
        payload["poster"] = validated_data.get("poster")
        payload["user"] = validated_data["user"]
        return MovieSerializer().create(payload)

    def to_representation(self, instance):
        return MovieSerializer().to_representation(instance)


class MoviePosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoviePoster
        fields = ["link", "primary", "movie"]
