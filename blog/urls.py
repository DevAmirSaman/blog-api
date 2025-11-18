from django.urls import path

from .views import PostList, PostDetail, TagList, TagDetail

urlpatterns = [
    path('posts/', PostList.as_view()),
    path('posts/<int:pk>/', PostDetail.as_view()),
    path('tags/', TagList.as_view()),
    path('tags/<str:name>/', TagDetail.as_view()),
]
