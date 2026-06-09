from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, CourseEnrollmentViewSet

router = DefaultRouter()
router.register(r'courses',     CourseViewSet,           basename='courses')
router.register(r'enrollments', CourseEnrollmentViewSet, basename='enrollments')

urlpatterns = [path('', include(router.urls))]