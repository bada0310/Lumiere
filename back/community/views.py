from django.db.models import Count, Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from Lumiere.api_pagination import list_response

from .models import Comment, CommentLike, Post, PostLike
from .serializers import CommentSerializer, PostSerializer


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if getattr(view, 'action', None) in {'comments', 'like'}:
            return True
        return obj.author == request.user


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = (
            Post.objects.select_related('author')
            .prefetch_related('products', 'likes')
            .annotate(
                comment_count=Count('comments', distinct=True),
                like_count=Count('likes', distinct=True),
            )
        )

        category = self.request.query_params.get('category')
        product_id = self.request.query_params.get('product')
        author_id = self.request.query_params.get('author')
        keyword = self.request.query_params.get('q')

        if category:
            queryset = queryset.filter(category=category)
        if product_id:
            queryset = queryset.filter(products__id=product_id)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) | Q(content__icontains=keyword)
            )

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        return list_response(request, self.get_queryset(), self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Post.objects.filter(pk=instance.pk).update(view_count=instance.view_count + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def mine(self, request):
        queryset = self.get_queryset().filter(author=request.user)
        return list_response(request, queryset, self.get_serializer_class())

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            return Response({'is_liked': False}, status=status.HTTP_200_OK)
        return Response({'is_liked': True}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        post = self.get_object()

        if request.method == 'GET':
            serializer = CommentSerializer(
                post.comments.filter(parent__isnull=True).select_related('author').prefetch_related(
                    'likes',
                    'replies',
                    'replies__author',
                    'replies__likes',
                ).annotate(
                    like_count=Count('likes', distinct=True),
                ),
                many=True,
                context={'request': request},
            )
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = CommentSerializer(
            data={**request.data, 'post': post.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = Comment.objects.select_related('post', 'author', 'parent').prefetch_related('likes').annotate(
            like_count=Count('likes', distinct=True),
        )
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def like(self, request, pk=None):
        comment = self.get_object()
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=request.user,
        )
        if not created:
            like.delete()
            return Response({'is_liked': False}, status=status.HTTP_200_OK)
        return Response({'is_liked': True}, status=status.HTTP_201_CREATED)
