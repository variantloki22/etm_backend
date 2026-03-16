from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'transactions', views.TicketTransactionViewSet, basename='transaction')
router.register(r'routes', views.BusRouteViewSet, basename='bus-routes')

urlpatterns = [
    path('', include(router.urls)),
]
