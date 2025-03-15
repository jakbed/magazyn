# rentals/admin.py
from django.contrib import admin
from .models import Category, Product, Komplet, Order, BorrowHistory, Serwis, Service, UserProfile
from import_export.admin import ImportExportModelAdmin
from import_export import resources



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


# Definiujemy klasę zasobu dla importu/eksportu
class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        exclude = ("id",)  # Django sam przypisze ID
        skip_unchanged = True  # Pomija duplikaty ID
        use_bulk = True  # Przyspiesza import

# Rejestrujemy model w Django Admin z obsługą importu/eksportu
@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):  # Dziedziczenie TYLKO z ImportExportModelAdmin
    resource_class = ProductResource
    list_display = ("brand", "model", "code")

@admin.register(Komplet)
class KompletAdmin(admin.ModelAdmin):
    list_display = ['name', 'status']
    filter_horizontal = ['products']  # użycie widgetu do wyboru wielu produktów
    list_filter = ['status']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'conference_code', 'status', 'reserved_at', 'pickup_date', 'return_date']
    list_filter = ['status', 'pickup_date', 'return_date']
    date_hierarchy = 'reserved_at'
    filter_horizontal = ['products', 'komplets']

@admin.register(BorrowHistory)
class BorrowHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'komplet', 'borrow_date', 'return_date']
    list_filter = ['borrow_date', 'return_date', 'user']

@admin.register(Serwis)
class SerwisAdmin(admin.ModelAdmin):

    list_display = ("name", "phone_number", "email", "street", "number", "postal_code", "city", "country")
    search_fields = ("name", "city", "phone_number", "email", "street", "postal_code", "country")
    ordering = ("name", "city")

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['product', 'komplet', 'reported_at', 'resolved', 'resolved_at', 'serwis']
    list_filter = ['resolved', 'reported_at', 'serwis']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'nickname']

