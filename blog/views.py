from datetime import datetime

from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .models import Post, Tag
from .permissions import IsOwnerOrReadOnly
from .serializers import PostSerializer, TagSerializer


class APIRoot(APIView):
    def get(self, request):
        return Response(
            {
                'posts': reverse('post-list', request=request),
                'tags': reverse('tag-list', request=request),
            }
        )


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
        user = (
            self.request.user if self.request.user.is_authenticated else None
        )

        queryset = (
            Post.objects.filter(
                Q(status='published', published_at__lte=timezone.now())
                | Q(author=user)
            )
            .select_related('author')
            .prefetch_related('tags')
        )

        query_params = self.request.query_params

        tags = query_params.getlist('tags')
        if len(tags) == 1:
            q = Q()
            for tag in tags[0].split(','):
                if tag := tag.strip():
                    q |= Q(tags__name__iexact=tag)
            queryset = queryset.filter(q)

        elif len(tags) > 1:
            for tag in tags:
                if tag := tag.strip():
                    queryset = queryset.filter(tags__name__iexact=tag)

        if author_username := query_params.get('author'):
            queryset = queryset.filter(
                author__username__iexact=author_username
            )

        published_after = query_params.get('published_after')
        published_before = query_params.get('published_before')

        date_format = '%Y-%m-%d'

        if published_after:
            try:
                published_after = datetime.strptime(
                    published_after, date_format
                ).date()
                queryset = queryset.filter(
                    published_at__date__gte=published_after
                )
            except ValueError:
                raise ValidationError(
                    {
                        'published_after': f'Invalid date format. Expected {date_format}.'
                    }
                )

        if published_before:
            try:
                published_before = datetime.strptime(
                    published_before, date_format
                ).date()
                queryset = queryset.filter(
                    published_at__date__lte=published_before
                )
            except ValueError:
                raise ValidationError(
                    {
                        'published_before': f'Invalid date format. Expected {date_format}.'
                    }
                )

        order_by_ownership = Case(
            When(author=user, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )

        order_by_status = Case(
            When(status='published', then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )

        return queryset.distinct().order_by(order_by_ownership, order_by_status, '-published_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_object(self):
        user = self.request.user
        pk = self.kwargs['pk']

        if not user.is_authenticated:
            return get_object_or_404(
                Post,
                pk=pk,
                status='published',
                published_at__lte=timezone.now()
            )

        if self.request.method == 'GET':
            queryset = Post.objects.filter(
                Q(status='published', published_at__lte=timezone.now())
                | Q(author=user)
            )
            return get_object_or_404(queryset, pk=pk)

        obj = get_object_or_404(Post, pk=pk)
        if obj.author != user:
            raise PermissionDenied('You do not have permission to modify this post.')

        return obj
