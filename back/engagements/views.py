from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from Lumiere.api_pagination import list_response

from .models import LikedProductOption, Notification
from .serializers import LikedProductOptionSerializer, NotificationSerializer


class LikedProductOptionViewSet(viewsets.ModelViewSet):
    serializer_class = LikedProductOptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LikedProductOption.objects.filter(user=self.request.user).select_related('product', 'product_option')

    def list(self, request, *args, **kwargs):
        return list_response(request, self.get_queryset(), self.get_serializer_class())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                instance = serializer.save()
        except IntegrityError:
            instance = self._get_existing_like(request)
            update_serializer = self.get_serializer(instance, data=request.data, partial=True)
            update_serializer.is_valid(raise_exception=True)
            instance = update_serializer.save()

        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)

    def _get_existing_like(self, request):
        product_id, option_id = self._like_lookup_values(request)
        return self.get_queryset().get(
            product_id=product_id,
            option_id=option_id,
        )

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        product_id, option_id = self._like_lookup_values(request)
        if not product_id:
            return Response({'detail': 'product_id or product_option_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        existing = self.get_queryset().filter(product_id=product_id, option_id=option_id).first()
        if existing:
            existing.delete()
            return Response({'is_liked': False}, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            {'is_liked': True, 'item': self.get_serializer(instance).data},
            status=status.HTTP_201_CREATED,
        )

    def _like_lookup_values(self, request):
        product_id = request.data.get('product_id')
        product_option_id = request.data.get('product_option_id')
        option_id = request.data.get('option_id', '')
        if product_option_id and not option_id:
            option_id = str(product_option_id)
        if product_option_id:
            try:
                from products.models import ProductOption

                product_id = ProductOption.objects.only('product_id').get(id=product_option_id).product_id
            except ProductOption.DoesNotExist:
                product_id = None
        return product_id, option_id


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_list(request):
    return list_response(
        request,
        Notification.objects.filter(user=request.user),
        NotificationSerializer,
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_unread_count(request):
    return Response(
        {
            'unread_count': Notification.objects.filter(user=request.user, read_at__isnull=True).count(),
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def notification_mark_all_read(request):
    now = timezone.now()
    updated = Notification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=now)
    return Response(
        {
            'updated': updated,
            'unread_count': 0,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['PATCH', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def notification_mark_read(request, pk):
    notification = Notification.objects.filter(user=request.user, pk=pk).first()
    if not notification:
        return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
    notification.mark_read()
    return Response(
        {
            'item': NotificationSerializer(notification, context={'request': request}).data,
            'unread_count': Notification.objects.filter(user=request.user, read_at__isnull=True).count(),
        },
        status=status.HTTP_200_OK,
    )
