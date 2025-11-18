from rest_framework import generics, permissions
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField, Q
from django.shortcuts import get_object_or_404

from .models import Post, Tag
from .serializers import PostSerializer, TagSerializer
from .permissions import IsOwnerOrReadOnly


class TagList(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self):
        name = self.kwargs['name']
        return get_object_or_404(Tag, name__iexact=name)


class PostList(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user if self.request.user.is_authenticated else None

        queryset = Post.objects.filter(
            Q(status='published', published_at__lte=timezone.now()) |
            Q(author=user)
        ).select_related('author').prefetch_related('tags')

        if tag_name := self.request.query_params.get('tag'):
            queryset = queryset.filter(tags__name__iexact=tag_name)

        queryset = queryset.annotate(
            is_owner=Case(
                When(author=user, then=Value(0)), 
                default=Value(1),
                output_field=IntegerField()
            )
        )

        return queryset.distinct().order_by('is_owner', '-published_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrReadOnly]
