from django.urls import reverse
from rest_framework import status
from django.utils import timezone


class TestPostList:
    def test_anonymous_user_sees_only_published_posts(self, api_client, published_post, draft_post):
        """Test that an anonymous user can only see published posts."""
        url = reverse('post-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == published_post.id

    def test_authenticated_user_sees_own_drafts_and_all_published_posts(self, api_client, user, published_post, draft_post, published_post_by_another_user, draft_post_by_another_user):
        """Test that an authenticated user can see their own drafts and all published posts."""
        api_client.force_authenticate(user=user)
        url = reverse('post-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

        returned_ids = {post['id'] for post in response.data['results']}
        # order is important
        expected_ids = {
            published_post.id,
            draft_post.id,
            published_post_by_another_user.id,
        }
        assert returned_ids == expected_ids

    def test_anonymous_user_cannot_create_post(self, api_client):
        """Test that an anonymous user cannot create a post."""
        url = reverse('post-list')
        data = {
            'title': 'New Post',
            'content': 'Content of the new post'
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authenticated_user_can_create_post_with_tags(self, api_client, user, tag_python, tag_django):
        """Test that an authenticated user can create a post with tags."""
        api_client.force_authenticate(user=user)
        url = reverse('post-list')
        data = {
            'title': 'New Post',
            'content': 'Content of the new post',
            'tags': [tag_python.id, tag_django.id],
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == data['title']
        assert response.data['author'] == user.username
        tag_ids = [tag for tag in response.data['tags']]
        assert tag_python.id in tag_ids
        assert tag_django.id in tag_ids

    def test_posts_are_ordered_by_ownership_then_status_then_published_at_desc(self, api_client, user, published_post, draft_post, published_post_by_another_user):
        """Test that posts are ordered by ownership, then status, then published_at descending."""
        api_client.force_authenticate(user=user)
        url = reverse('post-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        ids = [post['id'] for post in response.data['results']]
        # first the user's posts then other's published posts -> [ownership, status, -published_at]
        assert [published_post.id, draft_post.id, published_post_by_another_user.id] == ids


class TestPostFilters:
    def test_filter_by_single_tag(self, api_client, tag_python, published_post, published_post_by_another_user):
        """Test that filtering by a single tag returns correct posts."""
        published_post.tags.add(tag_python) # the other post has no tags initially

        url = reverse('post-list') + f'?tags={tag_python.name}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == published_post.id

    def test_filter_posts_by_multiple_tags_using_single_query_param_act_as_OR(self, api_client, tag_python, tag_django, published_post, published_post_by_another_user):
        """Test that filtering by multiple tags in a single query parameter acts as OR."""
        published_post.tags.add(tag_python)
        published_post_by_another_user.tags.add(tag_django)

        url = reverse('post-list') + f'?tags={tag_python.name},{tag_django.name}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_filter_posts_by_multiple_tags_using_multiple_query_params_act_as_AND(self, api_client, tag_python, tag_django, published_post, published_post_by_another_user):
        """Test that filtering by multiple tags using multiple query parameters acts as AND."""
        published_post.tags.add(tag_python)
        published_post_by_another_user.tags.add(tag_django)

        url = reverse('post-list') + f'?tags={tag_python.name}&tags={tag_django.name}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_filter_by_author_username(self, api_client, user, published_post, published_post_by_another_user):
        """Test that filtering by author username returns correct posts."""
        url = reverse('post-list') + f'?author={user.username}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == published_post.id

    def test_filter_posts_by_invalid_published_date_returns_400(self, api_client):
        """Test that filtering by invalid published date returns 400 Bad Request."""
        url = reverse('post-list') + '?published_before=invalid-date'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'published_before' in response.data

        url = reverse('post-list') + '?published_after=invalid-date'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'published_after' in response.data

    def test_filter_posts_by_published_date_range(self, api_client, published_post, published_post_by_another_user):
        """Test that filtering by published date range returns correct posts."""
        published_post.published_at = timezone.now() - timezone.timedelta(days=1)
        published_post.save()
        published_post_by_another_user.published_at = timezone.now() - timezone.timedelta(days=5)
        published_post_by_another_user.save()

        published_after = timezone.now() - timezone.timedelta(days=3)
        published_before = timezone.now() + timezone.timedelta(days=1)

        url = reverse('post-list') + f'?published_after={published_after.date()}&published_before={published_before.date()}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == published_post.id

    def test_filter_posts_by_published_after_only(self, api_client, published_post, published_post_by_another_user):
        """Test that filtering by published_after only returns correct posts."""
        published_after = timezone.now() - timezone.timedelta(days=10)

        url = reverse('post-list') + f'?published_after={published_after.date()}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_filter_posts_by_published_before_only(self, api_client, published_post, published_post_by_another_user):
        """Test that filtering by published_before only returns correct posts."""
        published_before = timezone.now() - timezone.timedelta(days=3)

        url = reverse('post-list') + f'?published_before={published_before.date()}'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


class TestPostDetail:
    def test_anonymous_user_can_read_published_post(self, api_client, published_post):
        """Test that an anonymous user can read a published post."""
        url = reverse('post-detail', args=[published_post.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == published_post.id

    def test_anonymous_user_cannot_read_draft_post(self, api_client, draft_post):
        """Test that an anonymous user cannot read a draft post."""
        url = reverse('post-detail', args=[draft_post.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_authenticated_user_can_read_own_published_post(self, api_client, user, published_post):
        """Test that an authenticated user can read their own published post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[published_post.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == published_post.id

    def test_authenticated_user_can_read_others_published_post(self, api_client, user, published_post_by_another_user):
        """Test that an authenticated user can read another user's published post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[published_post_by_another_user.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == published_post_by_another_user.id

    def test_authenticated_user_can_read_own_draft_post(self, api_client, user, draft_post):
        """Test that an authenticated user can read their own draft post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[draft_post.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == draft_post.id   

    def test_authenticated_user_cannot_read_others_draft_post(self, api_client, user, draft_post_by_another_user):
        """Test that an authenticated user cannot read another user's draft post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[draft_post_by_another_user.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_authenticated_user_can_delete_own_published_post(self, api_client, user, published_post):
        """Test that an authenticated user can delete their own published post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[published_post.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_authenticated_user_can_delete_own_draft_post(self, api_client, user, draft_post):
        """Test that an authenticated user can delete their own draft post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[draft_post.id])        
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT        

    def test_authenticated_user_cannot_delete_others_published_post(self, api_client, user, published_post_by_another_user):
        """Test that an authenticated user cannot delete another user's published post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[published_post_by_another_user.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authenticated_user_cannot_delete_others_draft_post(self, api_client, user, draft_post_by_another_user):
        """Test that an authenticated user cannot delete another user's draft post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[draft_post_by_another_user.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authenticated_user_can_update_own_post(self, api_client, user, published_post):
        """Test that an authenticated user can update their own post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[published_post.id])
        data = {
            'title': 'Updated Title',
            'content': 'Updated content'
        }
        response = api_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == data['title']
        assert response.data['content'] == data['content']
        assert response.data['author'] == user.username

    def test_authenticated_user_cannot_update_others_post(self, api_client, user, published_post_by_another_user):
        """Test that an authenticated user cannot update another user's post."""
        api_client.force_authenticate(user=user)
        url = reverse('post-detail', args=[published_post_by_another_user.id])
        data = {
            'title': 'Malicious Update',
            'content': 'Hacked content'
        }
        response = api_client.put(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTagList:
    def test_anonymous_user_can_list_tags(self, api_client, tag_python, tag_django):
        """Test that an anonymous user can list tags."""
        url = reverse('tag-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_authenticated_user_can_create_tag(self, api_client, user):
        """Test that an authenticated user can create a tag."""
        api_client.force_authenticate(user=user)
        url = reverse('tag-list')
        data = {
            'name': 'testing'
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']

    def test_anonymous_user_cannot_create_tag(self, api_client):
        """Test that an anonymous user cannot create a tag."""
        url = reverse('tag-list')
        data = {
            'name': 'testing'
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTagDetail:
    def test_anonymous_user_can_retrieve_tag(self, api_client, tag_python):
        """Test that an anonymous user can retrieve a tag."""
        url = reverse('tag-detail', args=[tag_python.name])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == tag_python.name

    def test_anonymous_user_cannot_update_tag(self, api_client, tag_python):
        """Test that an anonymous user cannot update a tag."""
        url = reverse('tag-detail', args=[tag_python.name])
        data = {
            'name': 'python-updated'
        }
        response = api_client.put(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_user_cannot_delete_tag(self, api_client, tag_python):
        """Test that an anonymous user cannot delete a tag."""
        url = reverse('tag-detail', args=[tag_python.name])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authenticated_user_can_update_tag(self, api_client, user, tag_python):
        """Test that an authenticated user can update a tag."""
        api_client.force_authenticate(user=user)
        url = reverse('tag-detail', args=[tag_python.name])
        data = {
            'name': 'python-updated'
        }
        response = api_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == data['name']

    def test_authenticated_user_can_delete_tag(self, api_client, user, tag_python):
        """Test that an authenticated user can delete a tag."""
        api_client.force_authenticate(user=user)
        url = reverse('tag-detail', args=[tag_python.name])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_tag_detail_is_case_insensitive(self, api_client, tag_python):
        """Test that tag detail retrieval is case-insensitive."""
        url = reverse('tag-detail', args=[tag_python.name.upper()])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == tag_python.name
