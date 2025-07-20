from django.urls import path
from . import views
from .views import (
    ItemDetailView,
    HomeView,
    add_to_cart,
    remove_from_cart,
    ShopView,
    OrderSummaryView,
    remove_single_item_from_cart,
    CheckoutView,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    CategoryView,
    about_view,
    contact_view,
)

app_name = 'core'

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    path('', views.landing_view, name='landing'),
    path('admin-redirect/', views.admin_redirect, name='admin_redirect'),
    path('chart-data/', views.chart_data, name='chart-data'),
    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('chart-data/', views.chart_data, name='chart-data'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('category/<slug>/', CategoryView.as_view(), name='category'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add_coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('shop/', ShopView.as_view(), name='shop'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart,
        name='remove-single-item-from-cart'),
    path('about/', about_view, name='about'),
    path('contact/', contact_view, name='contact'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund')
]
