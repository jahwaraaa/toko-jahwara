from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('health/', views.health_check, name='health_check'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<str:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<str:product_id>/delete/', views.product_delete, name='product_delete'),
    path('purchases/', views.purchase_history, name='purchase_history'),
    path('purchases/new/', views.purchase_create, name='purchase_create'),
    path('purchases/<str:purchase_id>/', views.purchase_detail, name='purchase_detail'),
]