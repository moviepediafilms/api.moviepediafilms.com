from rest_framework import serializers
from api.models import Profile, BadgeClaim
from api.constants import CLAIM_STATE
from django.db.models import Sum


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    amount_earned = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "type",
            "image",
            "email",
            "amount_earned",
            "level",
            "rank",
            "score",
            "mcoins",
            "pop_score",
        ]

    def get_type(self, profile: Profile):
        return profile.type.name

    def get_amount_earned(self, profile: Profile):
        return BadgeClaim.objects.filter(
            user=profile.user, state=CLAIM_STATE.SUCCESS
        ).aggregate(Sum("amount"))["amount__sum"]

    def get_email(self, profile: Profile):
        return profile.user.email

    def get_name(self, profile: Profile):
        return profile.user.get_fullname()

