from rest_framework import serializers

from products.models import Product, ProductOption
from products.serializers import ProductOptionSerializer, ProductSerializer

from .models import LikedProductOption, UrlAnalysisRecord


class LikedProductOptionSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source='product',
        queryset=Product.objects.all(),
        write_only=True,
        required=False,
    )
    product_option = ProductOptionSerializer(read_only=True)
    product_option_id = serializers.PrimaryKeyRelatedField(
        source='product_option',
        queryset=ProductOption.objects.select_related('product').all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = LikedProductOption
        fields = [
            'id',
            'product',
            'product_id',
            'product_option',
            'product_option_id',
            'option_id',
            'group_key',
            'brand',
            'name',
            'option',
            'image_url',
            'product_url',
            'snapshot',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'product', 'created_at', 'updated_at']

    def validate_snapshot(self, value):
        return value or {}

    def validate(self, attrs):
        product = attrs.get('product')
        product_option = attrs.get('product_option')
        if product_option and product and product_option.product_id != product.id:
            raise serializers.ValidationError('product_option_id must belong to product_id.')
        if product_option and not product:
            attrs['product'] = product_option.product
        if not attrs.get('product'):
            raise serializers.ValidationError('product_id or product_option_id is required.')
        return attrs

    def create(self, validated_data):
        product = validated_data['product']
        product_option = validated_data.get('product_option')
        if product_option:
            validated_data.setdefault('option_id', str(product_option.id))
            validated_data.setdefault(
                'option',
                ' '.join(part for part in [product_option.option_no, product_option.option_name] if part),
            )
        validated_data.setdefault('brand', product.brand)
        validated_data.setdefault('name', product.name)
        validated_data.setdefault('image_url', product.display_image_url)
        if product_option:
            offer = product_option.offers.filter(is_representative=True).first() or product_option.offers.order_by('price').first()
            if offer:
                validated_data.setdefault('product_url', offer.product_url)
        validated_data.setdefault('product_url', product.product_url)
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UrlAnalysisRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UrlAnalysisRecord
        fields = [
            'id',
            'source_url',
            'title',
            'brand',
            'product_name',
            'image_url',
            'colors',
            'result_payload',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_colors(self, value):
        return value or []

    def validate_result_payload(self, value):
        return value or {}

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
