from django.urls import path
from .views import EmployeeViewSet, DashboardStatsView

emp = EmployeeViewSet.as_view({'get':'list','post':'create'})
emp_detail = EmployeeViewSet.as_view({'get':'retrieve','patch':'update','delete':'destroy'})

urlpatterns = [
    path('',             emp),
    path('<int:pk>/',    emp_detail),
    path('dashboard-stats/', DashboardStatsView.as_view()),
]
