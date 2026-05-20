from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalaryViewSet, PayslipViewSet

router = DefaultRouter()
router.register(r'salary',   SalaryViewSet,  basename='salary')
router.register(r'payslips', PayslipViewSet, basename='payslip')

urlpatterns = [path('', include(router.urls))]