from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from api.constants import MOVIE_STATE
from api.models.movie import MovieList
from api.models import Contest, Movie


class ContestRecommendListSerializer(serializers.ModelSerializer):
    recommended = serializers.SerializerMethodField()
    movie = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.filter(state=MOVIE_STATE.PUBLISHED),
        write_only=True,
        error_messages={"does_not_exist": "Contest does not exist"},
    )

    class Meta:
        model = Contest
        fields = ["id", "name", "recommended", "max_recommends", "movie"]
        read_only_fields = ["name", "max_recommends", "movies"]

    def get_recommended(self, contest):
        request = self.context["request"]
        try:
            movie_list = MovieList.objects.get(
                name=contest.name, contest=contest, owner=request.user
            )
        except MovieList.DoesNotExist:
            return 0
        else:
            return movie_list.movies.count()

    def validate_movie(self, movie):
        action = self.context["action"]
        days = self.instance.days_per_movie
        recommend_till = movie.publish_on + timezone.timedelta(days=days)
        if action == "add" and timezone.now() >= recommend_till:
            raise ValidationError(
                f"Recommendation Period of this film for {self.instance.name} is now closed. Try other films."
            )
        return movie

    def validate(self, attrs):
        request = self.context["request"]
        action = self.context["action"]
        if not self.instance.is_live():
            raise ValidationError("Contest is not live")
        if attrs["movie"] not in self.instance.movies.all():
            raise ValidationError("Film hasn't participated in this contest")
        movie_list = MovieList.objects.filter(
            owner=request.user, contest=self.instance
        ).first()
        if (
            action == "add"
            and movie_list
            and self.instance.max_recommends <= movie_list.movies.count()
        ):
            raise ValidationError(
                f"You ran out of recommends ({self.instance.max_recommends}/{self.instance.max_recommends}) for {self.instance.name}. Undo the recommends from your profile to continue."
            )
        return super().validate(attrs)

    def update(self, contest, validated_data):
        user = self.context["request"].user
        action = self.context["action"]
        movie = validated_data["movie"]

        movie_list, _ = MovieList.objects.get_or_create(
            name=contest.name, owner=user, contest=contest
        )
        if action == "add":
            movie_list.movies.add(movie)
            movie.recommend_count += 1
            movie.save()
        elif action == "remove":
            movie_list.movies.remove(movie)
            movie.recommend_count = max(movie.recommend_count - 1, 0)
            movie.save()
        return contest
