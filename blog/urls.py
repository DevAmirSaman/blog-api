from django.urls import path

from .views import APIRoot, PostDetail, PostList, TagDetail, TagList

urlpatterns = [
    path('', APIRoot.as_view(), name='api-root'),
    path('posts/', PostList.as_view(), name='post-list'),
    path('posts/<int:pk>/', PostDetail.as_view(), name='post-detail'),
    path('tags/', TagList.as_view(), name='tag-list'),
    path('tags/<str:name>/', TagDetail.as_view(), name='tag-detail'),
]
