from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    product_id = serializers.UUIDField(source='product.id', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'product_id',
            'user_id',
            'username',
            'rating',
            'comment',
            'verified_purchase',
            'is_approved',
            'approved_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'product_id',
            'user_id',
            'username',
            'verified_purchase',
            'is_approved',
            'approved_at',
            'created_at',
            'updated_at',
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value

