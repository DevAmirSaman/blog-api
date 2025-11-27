from django.utils import timezone
from rest_framework import serializers

from .models import Post, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'author',
            'tags',
            'created_at',
            'updated_at',
            'published_at',
            'status',
            'content',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request', None)

        if request and request.method in ['POST', 'PUT', 'PATCH']:
            fields['tags'] = serializers.PrimaryKeyRelatedField(
                many=True, queryset=Tag.objects.all(), required=False
            )
        else:
            fields['tags'] = serializers.StringRelatedField(many=True)

        return fields

    def validate(self, data):
        status = data.get('status', getattr(self.instance, 'status', 'draft'))
        published_at = data.get(
            'published_at', getattr(self.instance, 'published_at', None)
        )

        if status == 'published' and published_at is None:
            raise serializers.ValidationError(
                {
                    'published_at': 'Published posts must have a publication date set.'
                }
            )

        if status == 'draft' and published_at is not None:
            data['status'] = 'published'

        if published_at and published_at > timezone.now():
            raise serializers.ValidationError(
                {
                    'published_at': "The publication date cannot be in the future for immediate publishing. Set status to 'draft' or omit the date for scheduling."
                }
            )

        if self.instance:
            if self.instance.status == 'published' and status == 'draft':
                data['published_at'] = None

        return data
