import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from blog.serializers import PostSerializer


class TestPostSerializer:
    def test_published_post_requires_published_at_date(self):
        """Test that a post with status 'published' must have a published_at date."""
        serializer = PostSerializer(
            data={
                'title': 'Test Post',
                'content': 'Content',
                'status': 'published',
                'published_at': None,
                'tags': [],
            }
        )

        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        error = exc.value.detail
        assert error['published_at'][
            0
        ].code == 'required' or 'must have' in str(error['published_at'][0])

    def test_auto_set_status_to_published_when_published_at_is_provided(self):
        """If published_at is provided (even in past), status should become 'published'."""
        serializer = PostSerializer(
            data={
                'title': 'Test Post',
                'content': 'Content',
                'status': 'draft',
                'published_at': '2024-01-01T10:00:00Z',
                'tags': [],
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data['status'] == 'published'

    def test_published_at_cannot_be_in_the_future(self):
        """Test that published_at date cannot be set in the future."""
        serializer = PostSerializer(
            data={
                'title': 'Test Post',
                'content': 'Content',
                'status': 'published',
                'published_at': timezone.now() + timezone.timedelta(days=1),
                'tags': [],
            }
        )

        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        error = exc.value.detail
        assert 'cannot be in the future' in error['published_at'][0]

    def test_status_transition_from_published_to_draft_clears_published_at(
        self, published_post
    ):
        """Test that changing status from 'published' to 'draft' clears published_at date."""
        serializer = PostSerializer(
            instance=published_post, data={'status': 'draft'}, partial=True
        )

        assert serializer.is_valid()
        validated_data = serializer.validated_data

        assert validated_data['status'] == 'draft'
        assert validated_data['published_at'] is None
