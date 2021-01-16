from rest_framework.exceptions import ValidationError
from api.constants import MOVIE_STATE
from api.models.movie import MovieList
from rest_framework import serializers
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
            movie_list = MovieList.objects.get(contest=contest, owner=request.user)
        except MovieList.DoesNotExist:
            return 0
        else:
            return movie_list.movies.count()

    def validate(self, attrs):
        if not self.instance.is_live():
            raise ValidationError("Contest is not live")
        if attrs["movie"] not in self.instance.movies.all():
            raise ValidationError("Film hasn't participated in this contest")
        return super().validate(attrs)

    def update(self, contest, validated_data):
        user = validated_data["user"]
        movie = validated_data["movie"]
        action = validated_data["action"]
        movie_list, _ = MovieList.objects.get_or_create(
            name=contest.name, owner=user, contest=contest
        )
        if action == "add":
            movie_list.movies.add(movie)
        elif action == "remove":
            movie_list.movies.remove(movie)
        return contest
