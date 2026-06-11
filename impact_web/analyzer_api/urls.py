# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze),
    path('impact/', views.impact),
     path('timeline/', views.timeline),
    path('report/', views.report),
    path('webhook/github/', views.github_webhook),
]