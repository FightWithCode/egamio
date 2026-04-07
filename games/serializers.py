from rest_framework import serializers
from .models import GameTag


class GameTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameTag
        fields = ['id', 'name', 'usage_count', 'is_featured']
