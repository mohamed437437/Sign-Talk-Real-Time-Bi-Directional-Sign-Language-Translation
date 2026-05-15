from rest_framework import serializers
from .models import Sign

class SignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sign
        fields = ['id', 'label', 'hand', 'created_at']
