
from django.urls import path
from . import views

urlpatterns = [
    # line callback
    path('callback/', views.callback),
    # 風險值
    path('out/', views.out_VaR),
]








