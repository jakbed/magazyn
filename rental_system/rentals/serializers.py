# rentals/serializers.py
from rest_framework import serializers
from .models import Category, Product, Komplet, Order, BorrowHistory, Serwis, Service, UserProfile

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()  # wyświetli nazwę kategorii
    class Meta:
        model = Product
        fields = ['id', 'brand', 'model', 'code', 'serial_number', 'description', 'status',
                  'category', 'quantity', 'weight', 'ean_code', 'image']

class KompletSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)  # zagnieżdżone produkty (tylko do odczytu)
    class Meta:
        model = Komplet
        fields = ['id', 'name', 'status', 'products']

class OrderSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    komplets = KompletSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()  # pokaże username
    class Meta:
        model = Order
        fields = ['id', 'user', 'conference_code', 'status', 'reserved_at', 'pickup_date', 'return_date', 'products', 'komplets']

class BorrowHistorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    # Pokazujemy nazwę produktu lub kompletu w zależności od tego, co było wypożyczone
    item = serializers.SerializerMethodField()
    def get_item(self, obj):
        return str(obj.product or obj.komplet)
    class Meta:
        model = BorrowHistory
        fields = ['id', 'user', 'item', 'borrow_date', 'return_date']

class SerwisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serwis
        fields = ['id', 'name', 'contact', 'address']

class ServiceSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField(required=False)
    komplet = serializers.StringRelatedField(required=False)
    serwis = SerwisSerializer(read_only=True)
    class Meta:
        model = Service
        fields = ['id', 'product', 'komplet', 'description', 'reported_at', 'resolved', 'resolved_at', 'serwis']

class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'nickname', 'avatar']
