from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'transactions', views.TicketTransactionViewSet, basename='transaction')
router.register(r'routes', views.RouteViewSet, basename='route')
router.register(r'buses', views.BusViewSet, basename='bus')

urlpatterns = [
    path('', include(router.urls)),
]
