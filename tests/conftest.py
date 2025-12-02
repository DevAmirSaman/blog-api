import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from blog.models import Post, Tag

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='password')


@pytest.fixture
def another_user(db):
    return User.objects.create_user(username='otheruser', password='password')


@pytest.fixture
def tag_python(db):
    return Tag.objects.create(name='python')


@pytest.fixture
def tag_django(db):
    return Tag.objects.create(name='Django')


@pytest.fixture
def draft_post(db, user):
    return Post.objects.create(
        title='Draft Post',
        content='Draft content',
        author=user,
        status='draft',
    )


@pytest.fixture
def published_post(db, user):
    return Post.objects.create(
        title='Published Post',
        content='Published content',
        author=user,
        status='published',
        published_at=timezone.now() - timezone.timedelta(days=1),
    )


@pytest.fixture
def published_post_by_another_user(db, another_user):
    return Post.objects.create(
        title='Another User Post',
        content='Content by another user',
        author=another_user,
        status='published',
        published_at=timezone.now() - timezone.timedelta(days=2),
    )


@pytest.fixture
def draft_post_by_another_user(db, another_user):
    return Post.objects.create(
        title='Another User Draft',
        content='Draft content by another user',
        author=another_user,
        status='draft',
    )
