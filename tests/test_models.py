import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from blog.models import Post, Tag


@pytest.mark.django_db
class TestPostModel:
    def test_slug_is_automatically_generated_from_title(self, user):
        """Test that slug is automatically generated from title on save."""
        post = Post(title='Test Title', content='Content', author=user)
        post.save()
        assert post.slug == 'test-title'

    def test_custom_slug_is_preserved_on_save(self, user):
        """Test that custom slug is preserved on save."""
        post = Post(
            title='Another Title',
            content='Content',
            author=user,
            slug='custom-slug',
        )
        post.save()
        assert post.slug == 'custom-slug'

    def test_draft_post_cannot_have_published_at_date(self, user):
        """Test that draft posts cannot have a publication date."""
        post = Post(
            title='Draft Post',
            content='Content',
            author=user,
            status='draft',
            published_at=timezone.now(),
        )

        with pytest.raises(ValidationError) as exc:
            post.clean()

        assert 'status' in exc.value.message_dict

    def test_published_post_requires_published_at_date(self, user):
        """Test that published posts must have a publication date."""
        post = Post(
            title='Published Post',
            content='Content',
            author=user,
            status='published',
            published_at=None,
        )

        with pytest.raises(ValidationError) as exc:
            post.clean()

        assert 'Published posts' in exc.value.message_dict['published_at'][0]

    def test_published_at_cannot_be_in_the_future(self, user):
        """Test that publication date cannot be in the future."""
        post = Post(
            title='Future Post',
            content='Content',
            author=user,
            status='published',
            published_at=timezone.now() + timezone.timedelta(days=1),
        )

        with pytest.raises(ValidationError) as exc:
            post.clean()

        assert (
            'cannot be in the future'
            in exc.value.message_dict['published_at'][0]
        )

    def test_post_string_representation_returns_title(self):
        """Test that the string representation of the Post model is the title."""
        post = Post(title='String Representation')

        assert str(post) == 'String Representation'


class TestTagModel:
    def test_tag_string_representation_returns_name(self):
        """Test that the string representation of the Tag model is the name."""
        tag = Tag(name='Django')

        assert str(tag) == 'Django'
