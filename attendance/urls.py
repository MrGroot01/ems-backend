from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet

router = DefaultRouter()#automatically creates the api
router.register(r'', AttendanceViewSet, basename='attendance')
urlpatterns = [path('', include(router.urls))]
