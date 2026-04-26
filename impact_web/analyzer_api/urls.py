from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze),
    path('impact/', views.impact),
     path('timeline/', views.timeline),
]