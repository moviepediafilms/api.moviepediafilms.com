from rest_framework import serializers
from api.models.payment import Package


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ["id", "active", "amount", "name", "description"]
