# rentals/urls.py
from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

# Router DRF dla endpointów API
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'komplets', views.KompletViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'borrow-history', views.BorrowHistoryViewSet, basename='borrowhistory')
router.register(r'services', views.ServiceViewSet)
router.register(r'serwisy', views.SerwisViewSet)
# Uwaga: powyższe rejestracje tworzą URL-e typu /api/products/, /api/orders/ etc.

app_name = 'rentals'
urlpatterns = [
    # Widoki aplikacji (HTML)
    path('', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('komplety/', views.KompletListView.as_view(), name='komplet_list'),
    path('komplety/<int:pk>/', views.KompletDetailView.as_view(), name='komplet_detail'),
    path('order/new/', views.OrderCreateView.as_view(), name='order_create'),
    path('dashboard/', views.UserDashboardView.as_view(), name='dashboard'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('service/new/', views.ServiceCreateView.as_view(), name='service_create'),
    # API endpoints
    path('api/', include(router.urls)),
]
